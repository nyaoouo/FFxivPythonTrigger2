from abc import ABC, abstractmethod
from collections.abc import Iterable
import struct
import zlib
from typing import Dict, Union, Iterator

from .pack import Pack, PackIdentifier
from .file import FileFactory, File
from .util import ConcurrentDictionary


def _compute_hash(s):
    return ~zlib.crc32(s.lower().encode()) & 0xFFFFFFFF


class IIndexFile(ABC):
    @property
    @abstractmethod
    def pack_id(self): return None

    @property
    @abstractmethod
    def file_key(self): return None

    @property
    @abstractmethod
    def offset(self): return None

    @property
    @abstractmethod
    def dat_file(self): return None


class IPackSource(Iterable):
    @abstractmethod
    def file_exists(self, path) -> bool:
        pass

    @abstractmethod
    def get_file(self, path) -> File:
        pass


class Directory(IPackSource):
    """
    Directory inside a SqPack.
    """

    @property
    def pack(self) -> Pack: return self._pack

    @property
    def index(self) -> 'IndexDirectory': return self._index

    @property
    def path(self):
        if self._path is None:
            return '/'.join([str(self.pack), '{:08X}'.format(self.index.key)])
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    def __init__(self, pack: Pack, index: 'IndexDirectory'):
        self._pack = pack
        self._index = index
        self._file_name_map = {}  # type: Dict[str, int]
        self._files = ConcurrentDictionary()  # type: ConcurrentDictionary[int, File]
        self._path = None

    def __repr__(self):
        return "Dir(%s)" % self.path

    def __str__(self):
        return self.path

    def file_exists(self, name_or_key):
        if isinstance(name_or_key, str):
            name_or_key = _compute_hash(name_or_key)
        return name_or_key in self.index.files

    def get_file(self, name_or_key) -> Union[type(None), File]:
        # NOTE: This function /can/ return None!
        def from_key(key):
            if key in self._files:
                return self._files[key]

            index = self.index.files.get(key)
            if index is None:
                return None
            file = FileFactory.get(self.pack, index)
            self._files[key] = file
            return file
        if isinstance(name_or_key, str):
            file = from_key(_compute_hash(name_or_key))
            if file is not None:
                file.path = "%s/%s" % (self.path, name_or_key)
            return file
        else:
            return from_key(name_or_key)

    def __iter__(self) -> Iterator[File]:
        for file_key in self.index.files.values():
            yield self.get_file(file_key)


class IndexDirectory(object):
    """
    Directory-entry inside an index file.
    """

    @property
    def pack_id(self) -> PackIdentifier: return self._pack_id

    @property
    def key(self) -> int: return self._key

    @property
    def offset(self) -> int: return self._offset

    @property
    def count(self) -> int: return self._count

    @property
    def files(self) -> Dict[int, 'IndexFile']: return self._files

    def __init__(self, pack_id, stream):
        self._files = {}  # type: Dict[int, 'IndexFile']
        self._pack_id = pack_id

        self._read_meta(stream)
        pos = stream.tell()
        self._read_files(stream)
        stream.seek(pos)

    def _read_meta(self, stream):
        self._key, self._offset, _len = struct.unpack('<Lll4x', stream.read(16))
        self._count = int(_len / 0x10)

    def _read_files(self, stream):
        stream.seek(self.offset)

        rem = self.count
        files = []
        while rem > 0:
            rem -= 1
            files += [IndexFile(self.pack_id, stream)]

        self._files = dict([(file.file_key, file) for file in files])

    def __repr__(self):
        return "IndexDir(dir_key=%08X)" % self.key


class IndexSource(IPackSource):
    @property
    def index(self) -> 'Index': return self._index

    @property
    def pack(self) -> Pack: return self._pack

    def __init__(self, pack: Pack, index: 'Index'):
        self._pack = pack
        self._index = index
        self._directories = {}  # type: Dict[int, Directory]
        self._directory_path_map = {}  # type: Dict[str, int]

    def __repr__(self):
        return "IndexSource(pack=%r)" % self.pack

    def directory_exists(self, path_or_key: Union[str, int]) -> bool:
        if isinstance(path_or_key, str):
            path_or_key = _compute_hash(path_or_key)
        return path_or_key in self.index.directories

    def get_directory(self, path_or_key: Union[str, int]) -> Directory:
        def from_key(key):
            if key in self._directories:
                return self._directories[key]

            index = self.index.directories.get(key)
            if index is None:
                return None
            directory = Directory(self.pack, index)
            self._directories[key] = directory
            return directory

        if isinstance(path_or_key, str):
            _dir = from_key(_compute_hash(path_or_key))
            if _dir is not None:
                _dir.path = path_or_key
            return _dir
        else:
            return from_key(path_or_key)

    def file_exists(self, path: str) -> bool:
        if '/' not in path:
            raise ValueError('path')

        last_separator = path.rindex('/')
        dir_path = path[:last_separator]
        base_name = path[last_separator + 1:]

        if self.directory_exists(dir_path):
            _dir = self.get_directory(dir_path)
            return _dir.file_exists(base_name)
        return False

    def get_file(self, path: str) -> File:
        if '/' not in path:
            raise ValueError('path')

        last_separator = path.rindex('/')
        dir_path = path[:last_separator]
        base_name = path[last_separator + 1:]
        _dir = self.get_directory(dir_path)
        if _dir is not None:
            return _dir.get_file(base_name)
        return None

    def get_file_from_keys(self, directory_key: int, file_key: int) -> File:
        _dir = self.get_directory(directory_key)
        if _dir is not None:
            return _dir.get_file(file_key)
        return None

    def __iter__(self):
        from itertools import chain
        for index in chain.from_iterable(map(lambda x: x.files.values(),
                                             self.index.directories.values())):
            try:
                _file = self.get_file_from_keys(index.directory_key, index.file_key)
                yield _file
            except TypeError:
                continue


class Index(object):
    """
    Class representing the data inside a *.index file.
    """

    @property
    def pack_id(self) -> PackIdentifier: return self._pack_id

    @property
    def header(self) -> 'IndexHeader': return self._header

    @property
    def directories(self) -> Dict[int, IndexDirectory]: return self._directories

    def __init__(self, pack_id, path_or_stream):
        self._pack_id = pack_id
        if isinstance(path_or_stream, str):
            with open(path_or_stream, 'rb') as stream:
                self._build(stream)
        else:
            self._build(path_or_stream)

    def _build(self, stream):
        SQPACKMAGIC = 0x00006B6361507153
        file_magic, = struct.unpack('<Q', stream.read(8))
        assert file_magic == SQPACKMAGIC

        self._read_header(stream)
        self._read_directories(stream)

    def _read_header(self, stream):
        HEADER_OFFSET_OFFSET = 0x0C

        stream.seek(HEADER_OFFSET_OFFSET)
        header_offset, = struct.unpack('<l', stream.read(4))

        stream.seek(header_offset)
        self._header = IndexHeader(stream)

    def _read_directories(self, stream):
        stream.seek(self.header.directories_offset)

        dirs = [IndexDirectory(self.pack_id, stream)
                for _ in range(self.header.directories_count)]

        self._directories = dict([(_dir.key, _dir) for _dir in dirs])


class IndexHeader(object):
    @property
    def directories_count(self): return self._directories_count

    @property
    def directories_offset(self): return self._directories_offset

    @property
    def files_count(self): return self._files_count

    @property
    def files_offset(self): return self._files_offset

    def __init__(self, stream):
        FILE_DATA_OFFSET = 0x08
        DIRECTORY_DATA_OFFSET = 0xE4

        start = stream.tell()

        stream.seek(start + FILE_DATA_OFFSET)
        self._files_offset, files_length = struct.unpack('<ll', stream.read(8))
        self._files_count = int(files_length / 0x10)

        stream.seek(start + DIRECTORY_DATA_OFFSET)
        self._directories_offset, dir_length = struct.unpack('<ll', stream.read(8))
        self._directories_count = int(dir_length / 0x10)


class IndexFile(IIndexFile):
    @property
    def pack_id(self): return self._pack_id

    @property
    def file_key(self): return self._file_key

    @property
    def directory_key(self): return self._directory_key

    @property
    def offset(self): return self._offset

    @property
    def dat_file(self): return self._dat_file

    def __init__(self, pack_id, stream):
        self._pack_id = pack_id
        self._file_key, self._directory_key = struct.unpack('<LL', stream.read(8))

        base_offset, = struct.unpack('<l4x', stream.read(8))
        self._dat_file = (base_offset & 0x7) >> 1
        self._offset = (base_offset & 0xFFFFFFF8) << 3

    def __hash__(self):
        return ((self.dat_file << 24) | hash(self._pack_id)) ^ self.offset

    def __eq__(self, other):
        if issubclass(other, IIndexFile):
            return other.pack_id == self.pack_id and \
                other.dat_file == self.dat_file and \
                other.offset == self.offset
        return False

    def __repr__(self):
        return "IndexFile(dir_key=%08X, file_key=%08X, dat_file=%u, offset=%08X)" % (self.directory_key,
                                                                                     self.file_key,
                                                                                     self.dat_file,
                                                                                     self.offset)


class Index2Source(IPackSource):
    @property
    def index(self): return self._index

    @property
    def pack(self): return self._pack

    def __init__(self, pack, index):
        self._pack = pack
        self._index = index
        self._files = {}
        self._file_path_map = {}

    def file_exists(self, path_or_hash):
        if isinstance(path_or_hash, str):
            path_or_hash = _compute_hash(path_or_hash)
        return path_or_hash in self.index.files

    def get_file(self, path_or_hash):
        def from_hash(hash):
            file = self._files.get(hash, None)
            if file is not None:
                return file

            index = self.index.files[hash]
            file = FileFactory.get(self.pack, index)
            self._files[hash] = file
            return file
        if isinstance(path_or_hash, str):
            f = from_hash(_compute_hash(path_or_hash))
            f.path = path_or_hash
            return f
        return from_hash(path_or_hash)

    def __iter__(self):
        for file in self.index.files.values():
            yield self.get_file(file.file_key)


class Index2(object):
    """
    Class representing the data inside a *.index2 file.
    """
    @property
    def header(self): return self._header

    @property
    def files(self): return self._files

    @property
    def pack_id(self): return self._pack_id

    def __init__(self, pack_id, path_or_stream):
        self._pack_id = pack_id
        if isinstance(path_or_stream, str):
            with open(path_or_stream, 'rb') as stream:
                self._build(stream)
        else:
            self._build(path_or_stream)

    def _build(self, stream):
        SQPACKMAGIC = 0x00006B6361507153
        file_magic, = struct.unpack('<Q', stream.read(8))
        assert file_magic == SQPACKMAGIC

        self._read_header(stream)
        self._read_files(stream)

    def _read_header(self, stream):
        HEADER_OFFSET_OFFSET = 0x0C

        stream.seek(HEADER_OFFSET_OFFSET)
        header_offset, = struct.unpack('<l', stream.read(4))

        stream.seek(header_offset)
        self._header = Index2Header(stream)

    def _read_files(self, stream):
        stream.seek(self.header.files_offset)

        files = [Index2File(self.pack_id, stream)
                 for _ in range(self.header.files_count)]
        # rem = self.header.files_count
        # files = []
        # while rem > 0:
        #     rem -= 1
        #     files += [Index2File(self.pack_id, stream)]

        self._files = dict([(file.file_key, file) for file in files])


class Index2Header(object):
    @property
    def files_count(self): return self._files_count

    @property
    def files_offset(self): return self._files_offset

    def __init__(self, stream):
        FILE_DATA_OFFSET = 0x08

        start = stream.tell()

        stream.seek(start + FILE_DATA_OFFSET)
        self._files_offset, files_length = struct.unpack('<ll', stream.read(8))
        self._files_count = int(files_length / 0x08)


class Index2File(IIndexFile):
    @property
    def pack_id(self): return self._pack_id

    @property
    def file_key(self): return self._file_key

    @property
    def offset(self): return self._offset

    @property
    def dat_file(self): return self._dat_file

    def __init__(self, pack_id, stream):
        self._pack_id = pack_id
        self._file_key, = struct.unpack('<L', stream.read(4))

        base_offset, = struct.unpack('<l', stream.read(4))
        self._dat_file = (base_offset & 0x7) >> 1
        self._offset = (base_offset & 0xFFFFFFF8) << 3

    def __hash__(self):
        return ((self.dat_file << 24) | hash(self._pack_id)) ^ self.offset

    def __eq__(self, other):
        if issubclass(other, IIndexFile):
            return other.pack_id == self.pack_id and \
                other.dat_file == self.dat_file and \
                other.offset == self.offset
        return False
