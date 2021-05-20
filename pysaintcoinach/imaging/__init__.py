import weakref
import io
import struct
from enum import Enum
from io import StringIO, BytesIO
from typing import Iterable, List, Callable, Dict

from PIL import Image

from ..file import File, FileCommonHeader
from ..indexfile import Directory
from ..pack import Pack
from .iconhelper import IconHelper


class ImageFormat(Enum):
    Unknown = 0
    A16R16G16B16Float = 0x2460

    A8R8G8B8_1 = 0x1131
    A8R8G8B8_2 = 0x1450
    A8R8G8B8_Cube = 0x1451
    A8R8G8B8_4 = 0x2150
    A8R8G8B8_5 = 0x4401

    A4R4G4B4 = 0x1440
    A1R5G5B5 = 0x1441
    R3G3B2 = 0x1130

    Dxt1 = 0x3420
    Dxt3 = 0x3430
    Dxt5 = 0x3431


class ImageHeader(object):
    @property
    def width(self) -> int: return self.__width

    @property
    def height(self) -> int: return self.__height

    @property
    def imgformat(self) -> ImageFormat: return self.__imgformat

    @property
    def end_of_header(self) -> int: return self.__end_of_header

    def __init__(self, stream: io.RawIOBase):
        LENGTH = 0x50
        FORMAT_OFFSET = 0x04
        WIDTH_OFFSET = 0x08
        HEIGHT_OFFSET = 0x0A

        self._buffer = stream.read(LENGTH)
        if len(self._buffer) != LENGTH:
            raise EOFError

        self.__width, = struct.unpack_from('<h', self._buffer, WIDTH_OFFSET)
        self.__height, = struct.unpack_from('<h', self._buffer, HEIGHT_OFFSET)
        self.__imgformat = ImageFormat(struct.unpack_from('<h',
                                                          self._buffer,
                                                          FORMAT_OFFSET)[0])
        self.__end_of_header = stream.tell()

    def get_buffer(self) -> bytes:
        return bytes(self._buffer)


class ImageFile(File):
    @property
    def image_header(self) -> ImageHeader: return self.__image_header

    @property
    def width(self) -> int: return self.image_header.width

    @property
    def height(self) -> int: return self.image_header.height

    @property
    def imgformat(self) -> ImageFormat: return self.image_header.imgformat

    def __init__(self,
                 pack: Pack,
                 common_header: FileCommonHeader):
        super(ImageFile, self).__init__(pack, common_header)
        self.__buffer_cache = None  # type: bytes
        self.__image_cache = None  # type: object
        stream = self._get_source_stream()
        stream.seek(common_header.end_of_header)
        self.__image_header = ImageHeader(stream)

    def get_image(self) -> Image.Image:
        if self.__image_cache is not None:
            return self.__image_cache

        image = ImageConverter.convert(self)

        # self.__image_cache = weakref.proxy(image)
        self.__image_cache = image
        return image

    def get_data(self) -> bytes:
        if self.__buffer_cache is not None:
            return self.__buffer_cache

        buffer = self._read()

        self.__buffer_cache = buffer

        return buffer

    def _read(self) -> bytes:
        source_stream = self._get_source_stream()
        offsets = self._get_block_offsets()

        data = b''
        with io.BytesIO() as data_stream:
            for offset in offsets:
                source_stream.seek(self.image_header.end_of_header + offset)
                self._read_block_into(source_stream, data_stream)
            data = data_stream.getvalue()
        return data

    def _get_block_offsets(self) -> Iterable[int]:
        COUNT_OFFSET = 0x14
        ENTRY_LENGTH = 0x14
        BLOCK_INFO_OFFSET = 0x18

        count, = struct.unpack_from('<h',
                                    self.common_header._buffer,
                                    COUNT_OFFSET)
        current_offset = 0
        offsets = []  # type: List[int]

        i = BLOCK_INFO_OFFSET + count * ENTRY_LENGTH
        while i + 2 <= len(self.common_header._buffer):
            _len, = struct.unpack_from('<H', self.common_header._buffer, i)
            if _len == 0:
                break
            offsets += [current_offset]
            current_offset += _len
            i += 2

        return offsets


class _ImageConverter(object):
    # Preprocessor = Callable[[bytes, bytearray, int, int], None]
    Preprocessor = Callable[[bytes, int, int], Image.Image]
    Preprocessors = {}  # type: Dict[ImageFormat, _ImageConverter.Preprocessor]

    def __new__(cls, *args):
        super().__new__(cls, *args)
        cls.Preprocessors = {
            #ImageFormat.A16R16G16B16Float: cls.process_A16R16G16B16Float,
            ImageFormat.A1R5G5B5: cls.process_A1R5G5B5,
            ImageFormat.A4R4G4B4: cls.process_A4R4G4B4,
            ImageFormat.A8R8G8B8_1: cls.process_A8R8G8B8,
            ImageFormat.A8R8G8B8_2: cls.process_A8R8G8B8,
            ImageFormat.A8R8G8B8_Cube: cls.process_A8R8G8B8,
            ImageFormat.A8R8G8B8_4: cls.process_A8R8G8B8,
            ImageFormat.A8R8G8B8_5: cls.process_A8R8G8B8,
            ImageFormat.Dxt1: cls.process_Dxt1,
            ImageFormat.Dxt3: cls.process_Dxt3,
            ImageFormat.Dxt5: cls.process_Dxt5,
            ImageFormat.R3G3B2: cls.process_R3G3B2,
        }
        return cls

    @classmethod
    def convert(cls, *args) -> Image.Image:
        if isinstance(args[0], ImageFile):
            file = args[0]  # type: ImageFile
            src = file.get_data()
            imgformat = file.imgformat
            height = file.height
            width = file.width
        else:
            file = None
            src = args[0]  # type: bytes
            imgformat = args[1]  # type: ImageFormat
            height = args[2]  # type: int
            width = args[3]  # type: int

        if imgformat not in cls.Preprocessors:
            return NotImplemented
        proc = cls.Preprocessors[imgformat]
        return proc(src, width, height)

    @classmethod
    def process_A1R5G5B5(cls, src: bytes, width: int, height: int):
        dst = bytearray()
        for v, in struct.iter_unpack('H', src):
            a = v & 0x8000
            r = v & 0x7C00
            g = v & 0x03E0
            b = v & 0x001F

            rgb = ((r << 9) | (g << 6) | (b << 3))
            argb_value = (a * 0x1FE00 | rgb | ((rgb >> 5) & 0x070707))
            # dst += bytes([(argb_value      ) & 0xFF,
            #               (argb_value >>  8) & 0xFF,
            #               (argb_value >> 16) & 0xFF,
            #               (argb_value >> 24) & 0xFF])
            dst += bytes([(argb_value >> 16) & 0xFF,  # R
                          (argb_value >>  8) & 0xFF,  # G
                          (argb_value      ) & 0xFF,  # B
                          (argb_value >> 24) & 0xFF]) # A

        image = Image.frombytes('RGBA', (width, height), bytes(dst))
        return image

        # dst += struct.pack('<4sLLLL56xLL4xLLLLLL16x',
        #                    b'DDS ', 124, 0x1007, height, width,
        #                    32, 0x41, 16, 0x7C00, 0x3E0, 0x1F, 0x8000, 0x1000)
        # dst += src

    @classmethod
    def process_A4R4G4B4(cls, src: bytes, width: int, height: int):
        dst = bytearray()
        for v, in struct.iter_unpack('H', src):
            # dst += bytes([((v      ) & 0x0F) << 4,
            #               ((v >>  4) & 0x0F) << 4,
            #               ((v >>  8) & 0x0F) << 4,
            #               ((v >> 12) & 0x0F) << 4])
            dst += bytes([((v >>  8) & 0x0F) << 4,
                          ((v >>  4) & 0x0F) << 4,
                          ((v      ) & 0x0F) << 4,
                          ((v >> 12) & 0x0F) << 4])

        image = Image.frombytes('RGBA', (width, height), bytes(dst))
        return image

        # dst += struct.pack('<4sLLLL56xLL4xLLLLLL16x',
        #                    b'DDS ', 124, 0x1007, height, width,
        #                    32, 0x41, 16, 0xF00, 0xF0, 0xF, 0xF000, 0x1000)
        # dst += src

    @classmethod
    def process_A8R8G8B8(cls, src: bytes, width: int, height: int):
        # dst += struct.pack('<4sLLLL56xLL4xLLLLLL16x',
        #                    b'DDS ', 124, 0x1007, height, width,
        #                    32, 0x41, 32, 0xFF0000, 0xFF00, 0xFF, 0xFF000000, 0x1000)
        # dst += src
        dst = bytearray()
        for v, in struct.iter_unpack('L', src):
            dst += bytes([((v >> 16) & 0xFF),
                          ((v >>  8) & 0xFF),
                          ((v      ) & 0xFF),
                          ((v >> 24) & 0xFF)])
        image = Image.frombytes('RGBA', (width, height), bytes(dst))
        return image

    @classmethod
    def process_Dxt1(cls, src: bytes, width: int, height: int):
        dst = bytearray()
        dst += struct.pack('<4sLLLL56xLL4s20xL16x',
                           b'DDS ', 124, 0x1007, height, width,
                           32, 0x04, b'DXT1', 0x1000)
        dst += src
        image = Image.open(BytesIO(dst))
        return image

    @classmethod
    def process_Dxt3(cls, src: bytes, width: int, height: int):
        dst = bytearray()
        dst += struct.pack('<4sLLLL56xLL4s20xL16x',
                           b'DDS ', 124, 0x1007, height, width,
                           32, 0x04, b'DXT3', 0x1000)
        dst += src
        image = Image.open(BytesIO(dst))
        return image

    @classmethod
    def process_Dxt5(cls, src: bytes, width: int, height: int):
        dst = bytearray()
        dst += struct.pack('<4sLLLL56xLL4s20xL16x',
                           b'DDS ', 124, 0x1007, height, width,
                           32, 0x04, b'DXT5', 0x1000)
        dst += src
        image = Image.open(BytesIO(dst))
        return image

    @classmethod
    def process_R3G3B2(cls, src: bytes, width: int, height: int):
        dst = bytearray()
        for v, in struct.iter_unpack('B', src):
            r = v & 0xE0
            g = v & 0x1C
            b = v & 0x03

            # dst += bytes([(b | (b << 2) | (b << 4) | (b << 6)) & 0xFF,
            #               (g | (g << 3) | (g << 6)) & 0xFF,
            #               (r | (r << 3) | (r << 6)) & 0xFF,
            #               0xFF])
            dst += bytes([(r | (r << 3) | (r << 6)) & 0xFF,
                          (g | (g << 3) | (g << 6)) & 0xFF,
                          (b | (b << 2) | (b << 4) | (b << 6)) & 0xFF])
        # dst += struct.pack('<4sLLLL56xLL4xLLLLLL16x',
        #                    b'DDS ', 124, 0x1007, height, width,
        #                    32, 0x02, 8, 0, 0, 0, 0xFF, 0x1000)
        # dst += src
        image = Image.frombytes('RGB', (width, height), bytes(dst))
        return image


ImageConverter = _ImageConverter()
