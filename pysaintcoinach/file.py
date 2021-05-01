from abc import ABC, abstractmethod
from enum import Enum
import io
import struct
import zlib
import weakref
import logging


logger = logging.getLogger(__name__)


class FileType(Enum):
    Unknown = 0
    Empty = 1
    Default = 2
    Model = 3
    Image = 4


class FileFactory(object):
    @staticmethod
    def get(pack, file):
        from .imaging import ImageFile

        stream = pack.get_data_stream(file.dat_file)
        stream.seek(file.offset)

        header = FileCommonHeader(file, stream)
        FILE_FACTORY_INIT_MAP = {
            FileType.Empty.value: EmptyFile,
            FileType.Default.value: FileDefault,
            FileType.Image.value: ImageFile,
            #FileType.Model.value: ModelFile,
        }

        if header.file_type not in FILE_FACTORY_INIT_MAP:
            raise TypeError("Unknown file type %02X" % header.file_type)
        return FILE_FACTORY_INIT_MAP[header.file_type](pack, header)


class FileCommonHeader(object):
    @property
    def index(self): return self._index

    @property
    def file_type(self): return self._file_type

    @property
    def end_of_header(self): return self._end_of_header

    def __len__(self): return self._length

    def __init__(self, index, stream):
        if index is None:
            raise ValueError('index')
        if stream is None:
            raise ValueError('stream')

        self._buffer = b''

        self._index = index

        self.__read(stream)

    def get_buffer(self):
        return self._buffer

    def __read(self, stream: io.RawIOBase):
        FILE_TYPE_OFFSET = 0x04
        FILE_LENGTH_OFFSET = 0x10
        FILE_LENGTH_SHIFT = 7

        self._buffer = stream.read(4)

        length, = struct.unpack_from('<l', self._buffer, 0)

        remaining = length - 4

        self._buffer += stream.read(remaining)

        self._file_type, = struct.unpack_from('<l', self._buffer, FILE_TYPE_OFFSET)
        self._length = struct.unpack_from('<l', self._buffer, FILE_LENGTH_OFFSET)[0] << FILE_LENGTH_SHIFT

        self._end_of_header = stream.tell()


class File(ABC):
    @property
    def pack(self): return self._pack

    @property
    def common_header(self) -> FileCommonHeader: return self._common_header

    @property
    def index(self): return self.common_header.index

    @property
    def path(self):
        if self._path is None:
            return "%08X" % self.index.file_key
        return self._path

    @path.setter
    def path(self, value): self._path = value

    def __init__(self, pack, common_header):
        self._path = None
        self._pack = pack
        self._common_header = common_header

    def __str__(self):
        return self.path

    def __repr__(self):
        return "File(%s)" % self.path

    @abstractmethod
    def get_data(self):
        pass

    def get_stream(self):
        return io.BytesIO(self.get_data())

    def _get_source_stream(self) -> io.RawIOBase:
        return self.pack.get_data_stream(self.index.dat_file)

    @staticmethod
    def _read_block(stream):
        with io.BytesIO() as out_stream:
            File._read_block_into(stream, out_stream)
            return out_stream.getvalue()

    @staticmethod
    def _read_block_into(in_stream: io.RawIOBase, out_stream: io.RawIOBase):
        MAGIC = 0x00000010

        HEADER_LENGTH = 0x10
        MAGIC_OFFSET = 0x00
        SOURCE_SIZE_OFFSET = 0x08
        RAW_SIZE_OFFSET = 0x0C

        BLOCK_PADDING = 0x80

        COMPRESSION_THRESHOLD = 0x7D00

        # Block:
        # 10h   Header
        # *     Data
        #
        # Header:
        # 4h    Magic
        # 4h    Unknown / Zero
        # 4h    Size in source
        # 4h    Raw size
        # -> If size in source >= 7D00h then data is uncompressed

        header = in_stream.read(HEADER_LENGTH)
        if len(header) != HEADER_LENGTH:
            raise EOFError

        magic_check, = struct.unpack_from('<l', header, MAGIC_OFFSET)
        source_size, = struct.unpack_from('<l', header, SOURCE_SIZE_OFFSET)
        raw_size, = struct.unpack_from('<l', header, RAW_SIZE_OFFSET)

        if magic_check != MAGIC:
            raise NotImplementedError("Magic number not present")

        is_compressed = source_size < COMPRESSION_THRESHOLD

        block_size = source_size if is_compressed else raw_size

        if is_compressed and ((block_size + HEADER_LENGTH) % BLOCK_PADDING) != 0:
            block_size += BLOCK_PADDING - ((block_size + HEADER_LENGTH) % BLOCK_PADDING)

        buffer = in_stream.read(block_size)
        if len(buffer) != block_size:
            raise EOFError

        if is_compressed:
            current_position = out_stream.tell()
            if raw_size != out_stream.write(zlib.decompress(buffer, -15)):
                raise RuntimeError("Inflated block does not match indicated size")
        else:
            out_stream.write(buffer)

    def __hash__(self):
        return hash(self.index)

    def __eq__(self, other):
        if isinstance(other, File):
            return other.index == self.index
        return False


class EmptyFile(File):
    def __init__(self, pack, header):
        super().__init__(pack, header)

    def get_data(self):
        return b''


class FileDefault(File):
    def __init__(self, pack, header):
        super().__init__(pack, header)
        self._buffer_cache = None

    def get_data(self):
        if self._buffer_cache is not None:
            return self._buffer_cache

        logger.info('Getting data for: %s' % self.path)
        buffer = self.__read()

        self._buffer_cache = buffer

        return buffer

    def __read(self):
        BLOCK_COUNT_OFFSET = 0x14
        BLOCK_INFO_OFFSET = 0x18
        BLOCK_INFO_LENGTH = 0x08

        source_stream = self._get_source_stream()
        block_count, = struct.unpack_from('<h', self.common_header._buffer, BLOCK_COUNT_OFFSET)

        with io.BytesIO(b'\0' * len(self.common_header)) as data_stream:
            for i in range(0, block_count):
                block_offset, = struct.unpack_from('<l',
                                                   self.common_header._buffer,
                                                   BLOCK_INFO_OFFSET + i * BLOCK_INFO_LENGTH)
                source_stream.seek(self.common_header.end_of_header + block_offset)
                File._read_block_into(source_stream, data_stream)

            return data_stream.getvalue()
