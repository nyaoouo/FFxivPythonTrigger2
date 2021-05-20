from typing import Iterable as IterableT, Sequence as SequenceT
from struct import unpack_from

from .language import Language
from .column import Column
from ..file import File
from .. import ex


class Header(object):

    LANGUAGE_MAP = {0: Language.none,
                    1: Language.japanese,
                    2: Language.english,
                    3: Language.german,
                    4: Language.french,
                    5: Language.chinese_simplified,
                    6: Language.chinese_traditional,
                    7: Language.korean}

    @property
    def collection(self) -> 'ex.ExCollection':
        return self.__collection

    @property
    def file(self) -> File:
        return self.__file

    @property
    def name(self) -> str:
        return self.__name

    @property
    def variant(self) -> int:
        return self.__variant

    @property
    def columns(self) -> IterableT[Column]:
        return self.__columns

    @property
    def column_count(self) -> int:
        return len(self.__columns)

    @property
    def data_file_ranges(self) -> IterableT[range]:
        return self.__data_file_ranges

    @property
    def available_languages(self) -> IterableT[Language]:
        return self.__available_languages

    @property
    def available_languages_count(self) -> int:
        return len([x for x in self.__available_languages if x != Language.none])

    @property
    def fixed_size_data_length(self) -> int:
        return self.__fixed_size_data_length

    def __init__(self, collection: 'ex.ExCollection', name: str, file: File):
        self.__available_languages = []
        self.__columns = []
        self.__data_file_ranges = []

        self.__collection = collection
        self.__name = name
        self.__file = file

        self.__build()

    def get_column(self, index: int) -> Column:
        return self.__columns[index]

    def create_column(self, index: int, data: bytes, offset: int) -> Column:
        return Column(self, index, data, offset)

    def __build(self):
        MAGIC = 0x46485845
        MINIMUM_LENGTH = 0x2E
        FIXED_SIZE_DATA_LENGTH_OFFSET = 0x06
        VARIANT_OFFSET = 0x10
        DATA_OFFSET = 0x20

        buffer = self.file.get_data()

        if len(buffer) < MINIMUM_LENGTH:
            raise ValueError("EXH file is too short")
        if unpack_from("<L", buffer, 0)[0] != MAGIC:
            raise ValueError("File not a EX header")

        self.__fixed_size_data_length, = unpack_from(">H", buffer, FIXED_SIZE_DATA_LENGTH_OFFSET)
        self.__variant, = unpack_from(">H", buffer, VARIANT_OFFSET)
        if self.variant not in [1, 2]:
            raise NotImplementedError("Variant %u not supported" % self.variant)

        current_position = DATA_OFFSET
        current_position = self.__read_columns(buffer, current_position)
        current_position = self.__read_partial_files(buffer, current_position)
        self.__read_suffixes(buffer, current_position)

    def __read_columns(self, buffer: bytes, position):
        COUNT_OFFSET = 0x08
        LENGTH = 0x04

        count, = unpack_from(">H", buffer, COUNT_OFFSET)
        self.__columns = []
        for i in range(count):
            self.__columns += [self.create_column(i, buffer, position)]
            position += LENGTH

        return position

    def __read_partial_files(self, buffer: bytes, position):
        COUNT_OFFSET = 0x0A
        LENGTH = 0x08

        count, = unpack_from(">H", buffer, COUNT_OFFSET)
        self.__data_file_ranges = []
        for i in range(count):
            _min, _len = unpack_from(">ll", buffer, position)
            self.__data_file_ranges += [range(_min, _min + _len)]
            position += LENGTH

        return position

    def __read_suffixes(self, buffer: bytes, position):
        COUNT_OFFSET = 0x0C
        LENGTH = 0x02

        count, = unpack_from(">H", buffer, COUNT_OFFSET)
        self.__available_languages = []
        for i in range(count):
            lang = self.LANGUAGE_MAP[buffer[position]]
            position += LENGTH
            if lang != Language.unsupported:
                self.__available_languages += [lang]

        return
