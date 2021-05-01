from enum import Enum
from typing import List
from construct import Struct, Const, Int16ul, Int16ub, Int32ul, Int32ub, BytesInteger
from struct import unpack_from, pack
from abc import abstractmethod

from ..file import File


class ScdCodec(Enum):
    OGG = 0x06
    MSADPCM = 0x0C


class ScdOggCryptType(Enum):
    none = 0x0000
    VorbisHeaderXor = 0x2002
    FullXorUsingTable = 0x2003


class ScdEntry(object):
    @property
    def file(self): return self._file
    @property
    def header(self): return self._header

    def __init__(self, file, header):
        self._file = file
        self._header = header

    @abstractmethod
    def get_decoded(self) -> bytes:
        pass


class ScdAdpcmEntry(ScdEntry):
    def __init__(self, file, header, chunks_offset, data_offset):
        super(ScdAdpcmEntry, self).__init__(file, header)
        self._decode(chunks_offset, data_offset)

    def get_decoded(self):
        return self._decoded

    def _decode(self, chunks_offset, data_offset):
        WAVE_HEADER_SIZE = 0x10

        wav_header_offset = data_offset
        final_data_offset = chunks_offset + self.header.samples_offset

        self._decoded = bytearray()
        self._decoded += b'RIFF'
        self._decoded += pack('<L', 0x14 + WAVE_HEADER_SIZE + self.header.data_size)
        self._decoded += b'WAVEfmt '
        self._decoded += pack('<L', WAVE_HEADER_SIZE)
        self._decoded += self.file._input_buffer[wav_header_offset:wav_header_offset + WAVE_HEADER_SIZE]
        self._decoded += b'data'
        self._decoded += pack('<L', self.header.data_size)
        self._decoded += self.file._input_buffer[final_data_offset:final_data_offset + self.header.data_size]


class ScdOggEntry(ScdEntry):
    XOR_TABLE = [
        0x3A, 0x32, 0x32, 0x32, 0x03, 0x7E, 0x12, 0xF7,
        0xB2, 0xE2, 0xA2, 0x67, 0x32, 0x32, 0x22, 0x32,
        0x32, 0x52, 0x16, 0x1B, 0x3C, 0xA1, 0x54, 0x7B,
        0x1B, 0x97, 0xA6, 0x93, 0x1A, 0x4B, 0xAA, 0xA6,
        0x7A, 0x7B, 0x1B, 0x97, 0xA6, 0xF7, 0x02, 0xBB,
        0xAA, 0xA6, 0xBB, 0xF7, 0x2A, 0x51, 0xBE, 0x03,
        0xF4, 0x2A, 0x51, 0xBE, 0x03, 0xF4, 0x2A, 0x51,
        0xBE, 0x12, 0x06, 0x56, 0x27, 0x32, 0x32, 0x36,
        0x32, 0xB2, 0x1A, 0x3B, 0xBC, 0x91, 0xD4, 0x7B,
        0x58, 0xFC, 0x0B, 0x55, 0x2A, 0x15, 0xBC, 0x40,
        0x92, 0x0B, 0x5B, 0x7C, 0x0A, 0x95, 0x12, 0x35,
        0xB8, 0x63, 0xD2, 0x0B, 0x3B, 0xF0, 0xC7, 0x14,
        0x51, 0x5C, 0x94, 0x86, 0x94, 0x59, 0x5C, 0xFC,
        0x1B, 0x17, 0x3A, 0x3F, 0x6B, 0x37, 0x32, 0x32,
        0x30, 0x32, 0x72, 0x7A, 0x13, 0xB7, 0x26, 0x60,
        0x7A, 0x13, 0xB7, 0x26, 0x50, 0xBA, 0x13, 0xB4,
        0x2A, 0x50, 0xBA, 0x13, 0xB5, 0x2E, 0x40, 0xFA,
        0x13, 0x95, 0xAE, 0x40, 0x38, 0x18, 0x9A, 0x92,
        0xB0, 0x38, 0x00, 0xFA, 0x12, 0xB1, 0x7E, 0x00,
        0xDB, 0x96, 0xA1, 0x7C, 0x08, 0xDB, 0x9A, 0x91,
        0xBC, 0x08, 0xD8, 0x1A, 0x86, 0xE2, 0x70, 0x39,
        0x1F, 0x86, 0xE0, 0x78, 0x7E, 0x03, 0xE7, 0x64,
        0x51, 0x9C, 0x8F, 0x34, 0x6F, 0x4E, 0x41, 0xFC,
        0x0B, 0xD5, 0xAE, 0x41, 0xFC, 0x0B, 0xD5, 0xAE,
        0x41, 0xFC, 0x3B, 0x70, 0x71, 0x64, 0x33, 0x32,
        0x12, 0x32, 0x32, 0x36, 0x70, 0x34, 0x2B, 0x56,
        0x22, 0x70, 0x3A, 0x13, 0xB7, 0x26, 0x60, 0xBA,
        0x1B, 0x94, 0xAA, 0x40, 0x38, 0x00, 0xFA, 0xB2,
        0xE2, 0xA2, 0x67, 0x32, 0x32, 0x12, 0x32, 0xB2,
        0x32, 0x32, 0x32, 0x32, 0x75, 0xA3, 0x26, 0x7B,
        0x83, 0x26, 0xF9, 0x83, 0x2E, 0xFF, 0xE3, 0x16,
        0x7D, 0xC0, 0x1E, 0x63, 0x21, 0x07, 0xE3, 0x01]

    def __init__(self, file, header, data_offset):
        super(ScdOggEntry, self).__init__(file, header)
        self._decode(data_offset)

    def get_decoded(self):
        return self._decoded

    def _decode(self, data_offset):
        CRYPT_TYPE_OFFSET = 0x00
        XOR_VALUE_OFFSET = 0x02
        SEEK_TABLE_SIZE_OFFSET = 0x10
        VORBIS_HEADER_SIZE_OFFSET = 0x14

        crypt_type = ScdOggCryptType(self.file._read_int16(data_offset + CRYPT_TYPE_OFFSET))

        seek_table_size = self.file._read_int32(data_offset + SEEK_TABLE_SIZE_OFFSET)
        vorbis_header_size = self.file._read_int32(data_offset + VORBIS_HEADER_SIZE_OFFSET)

        vorbis_header_offset = data_offset + 0x20 + seek_table_size
        sound_data_offset = vorbis_header_offset + vorbis_header_size

        vorbis_header = self.file._input_buffer[vorbis_header_offset:vorbis_header_offset + vorbis_header_size]

        if crypt_type == ScdOggCryptType.VorbisHeaderXor:
            xor_val = self.file._input_buffer[data_offset + XOR_VALUE_OFFSET]
            if xor_val != 0:
                vorbis_header = bytes(map(lambda b: b ^ xor_val, vorbis_header))

        self._decoded = bytearray()
        self._decoded += vorbis_header
        self._decoded += self.file._input_buffer[sound_data_offset:sound_data_offset + self.header.data_size]

        if crypt_type == ScdOggCryptType.FullXorUsingTable:
            self._xor_using_table()

    def _xor_using_table(self):
        static_xor = self.header.data_size & 0x7F
        table_offset = self.header.data_size & 0x3F
        for i in range(len(self._decoded)):
            self._decoded[i] ^= self.XOR_TABLE[(table_offset + i) & 0xFF]
            self._decoded[i] ^= static_xor


class ScdFile(object):
    @property
    def source_file(self) -> File: return self._source_file
    @property
    def scd_header(self): return self._scd_header
    @property
    def entry_headers(self): return self._entry_headers
    @property
    def entries(self): return self._entries

    def __init__(self, source_file: File):
        self._use_little_endian = False
        self._source_file = source_file
        self._input_buffer = None
        self._decode()

    def _decode(self):
        self._input_buffer = self.source_file.get_data()

        self._init()

        file_header_size = self._read_int16(0x0E)

        self._read_scd_header(file_header_size)

        self._entry_headers = []
        entry_chunk_offsets = []
        entry_data_offsets = []
        for i in range(self.scd_header.entry_count):
            header_offset = self._read_int32(self.scd_header.entry_table_offset + 4 * i)
            entry_header = self._read_entry_header(header_offset)
            self._entry_headers += [entry_header]

            entry_chunk_offsets += [header_offset + 0x20]
            data_offset = header_offset + 0x20
            for j in range(entry_header.aux_chunk_count):
                data_offset += self._read_int32(data_offset + 4)
            entry_data_offsets += [data_offset]

        self._entries = []
        for i in range(self.scd_header.entry_count):
            self._entries += [self._create_entry(self._entry_headers[i],
                                                 entry_chunk_offsets[i],
                                                 entry_data_offsets[i])]

    def _init(self):
        # Check file header magic
        if self._input_buffer[0:8] != b'SEDBSSCF':
            raise RuntimeError('Invalid data: magic')

        if unpack_from('<L', self._input_buffer, 0x08)[0] in [2, 3]:
            self._use_little_endian = True
        elif unpack_from('>L', self._input_buffer, 0x08)[0] in [2, 3]:
            print('WARNING: %s uses big-endian format???' % self.source_file.path)
            self._use_little_endian = False
        else:
            raise RuntimeError('Invalid data: version')

    def _read_scd_header(self, offset):
        self._scd_header = Struct(BytesInteger(2, swapped=self._use_little_endian),
                                  BytesInteger(2, swapped=self._use_little_endian),
                                  'entry_count' / BytesInteger(2, swapped=self._use_little_endian),
                                  BytesInteger(2, swapped=self._use_little_endian),
                                  BytesInteger(4, swapped=self._use_little_endian),
                                  'entry_table_offset' / BytesInteger(4, swapped=self._use_little_endian),
                                  BytesInteger(4, swapped=self._use_little_endian),
                                  BytesInteger(4, swapped=self._use_little_endian),
                                  BytesInteger(4, swapped=self._use_little_endian))\
            .parse(self._input_buffer[offset:])

    def _read_entry_header(self, offset):
        return Struct('data_size' / BytesInteger(4, swapped=self._use_little_endian),
                      'channel_count' / BytesInteger(4, swapped=self._use_little_endian),
                      'frequency' / BytesInteger(4, swapped=self._use_little_endian),
                      'codec' / BytesInteger(4, swapped=self._use_little_endian),
                      'loop_start_sample' / BytesInteger(4, swapped=self._use_little_endian),
                      'loop_end_sample' / BytesInteger(4, swapped=self._use_little_endian),
                      'samples_offset' / BytesInteger(4, swapped=self._use_little_endian),
                      'aux_chunk_count' / BytesInteger(2, swapped=self._use_little_endian),
                      BytesInteger(2, swapped=self._use_little_endian))\
            .parse(self._input_buffer[offset:])

    def _create_entry(self, header, chunks_offset, data_offset):
        if header.data_size == 0 or header.codec == 0:
            return None
        if header.codec == ScdCodec.OGG.value:
            return ScdOggEntry(self, header, data_offset)
        elif header.codec == ScdCodec.MSADPCM.value:
            return ScdAdpcmEntry(self, header, chunks_offset, data_offset)
        else:
            raise NotImplementedError()

    def _read_int16(self, offset):
        return unpack_from('<H' if self._use_little_endian else '>H', self._input_buffer, offset)[0]

    def _read_int32(self, offset):
        return unpack_from('<L' if self._use_little_endian else '>L', self._input_buffer, offset)[0]

    def _read_int64(self, offset):
        return unpack_from('<Q' if self._use_little_endian else '>Q', self._input_buffer, offset)[0]
