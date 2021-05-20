from typing import Union, Tuple, Iterable as IterableT, TypeVar, Type, Dict
from abc import abstractmethod
from struct import unpack_from
from collections import OrderedDict
from threading import Lock

from ..file import File
from .sheet import IRow, ISheet
from .language import Language
from .header import Header
from .. import ex
from ..util import ConcurrentDictionary


class IDataRow(IRow):
    @property
    @abstractmethod
    def offset(self) -> int:
        pass

    @property
    @abstractmethod
    def sheet(self) -> 'IDataSheet':
        pass

T = TypeVar('T', bound=IDataRow)


class IDataSheet(ISheet[T]):
    @property
    @abstractmethod
    def language(self) -> Language:
        pass

    @abstractmethod
    def get_buffer(self) -> bytes:
        pass


class DataRowBase(IDataRow):
    @property
    def sheet(self) -> Union[IDataSheet, ISheet]: return self.__sheet

    @property
    def key(self): return self.__key

    @property
    def offset(self): return self.__offset

    def __init__(self, sheet: IDataSheet, key: int, offset: int):
        self.__sheet = sheet
        self.__key = key
        self.__offset = offset
        self.__value_references = {}  # type: Dict[int, object]

    def __getitem__(self, item: int):
        if not isinstance(item, int):
            raise ValueError('item must be an int')
        column_index = item

        value = self.__value_references.get(column_index)
        if value is not None:
            return value

        column = self.sheet.header.get_column(column_index)
        value = column.read(self.sheet.get_buffer(), self)
        self.__value_references[column_index] = value

        return value

    def get_raw(self, column_index: int, **kwargs):
        column = self.sheet.header.get_column(column_index)
        return column.read_raw(self.sheet.get_buffer(), self)

    def column_values(self) -> IterableT[object]:
        buffer = self.sheet.get_buffer()
        for column in self.sheet.header.columns:
            yield column.read(buffer, self)

    def items(self):
        item_dict = OrderedDict()
        for c in self.sheet.header.columns:
            item_dict[c.name] = self[c.index]
        return item_dict


class PartialDataSheet(IDataSheet[T]):
    @property
    def source_sheet(self): return self.__source_sheet

    @property
    def range(self): return self.__range

    @property
    def file(self): return self.__file

    @property
    def keys(self): return self.__row_offsets.keys()

    @property
    def language(self): return self.source_sheet.language

    @property
    def name(self): return self.source_sheet.name + "_" + str(self.range.start)

    @property
    def header(self): return self.source_sheet.header

    @property
    def collection(self): return self.source_sheet.collection

    def __init__(self,
                 t_cls: Type[T],
                 source_sheet: IDataSheet[T],
                 _range: range,
                 file: File):
        self.__rows = None  # type: ConcurrentDictionary[int, T]
        self.__row_offsets = {}
        self.__source_sheet = source_sheet
        self.__range = _range
        self.__file = file
        self.__t_cls = t_cls

        self.__build()

    def get_buffer(self):
        return self.file.get_data()

    def __build(self):
        HEADER_LENGTH_OFFSET = 0x08
        ENTRIES_OFFSET = 0x20
        ENTRY_LENGTH = 0x08
        ENTRY_KEY_OFFSET = 0x00
        ENTRY_POSITION_OFFSET = 0x04

        buffer = self.file.get_data()

        header_len, = unpack_from(">l", buffer, HEADER_LENGTH_OFFSET)
        count = int(header_len / ENTRY_LENGTH)
        current_position = ENTRIES_OFFSET

        self.__rows = ConcurrentDictionary()
        for i in range(count):
            key, = unpack_from(">l", buffer, current_position + ENTRY_KEY_OFFSET)
            off, = unpack_from(">l", buffer, current_position + ENTRY_POSITION_OFFSET)
            self.__row_offsets[key] = off
            #self.__rows[key] = self._create_row(key, off)
            current_position += ENTRY_LENGTH

    def _create_row(self, key, offset) -> T:
        return self.__t_cls(self, key, offset)

    def get_all_rows(self) -> IterableT[T]:
        return self.__rows.values()

    def __getitem__(self, item: Union[int, Tuple[int, int]]) -> Union[T, IRow, object]:
        def get_row(key):
            def _add_value(k):
                offset = self.__row_offsets[key]
                if offset is not None:
                    return self._create_row(k, offset)
                else:
                    return None  # there is no default for T.
            return self.__rows.get_or_add(key, _add_value)

        if isinstance(item, tuple):
            return get_row(item[0])[item[1]]
        else:
            return get_row(item)

    def __contains__(self, item):
        return item in self.__row_offsets

    def __len__(self):
        return len(self.__row_offsets)

    def __iter__(self):
        for key, off in self.__row_offsets.items():
            yield self.__rows.get_or_add(key, lambda k: self._create_row(k, off))


class DataSheet(IDataSheet[T]):
    @property
    def collection(self): return self.__collection

    @property
    def header(self): return self.__header

    @property
    def language(self): return self.__language

    @property
    def name(self): return self.header.name + self.language.get_suffix()

    def __init__(self,
                 t_cls: Type[T],
                 collection: 'ex.ExCollection',
                 header: Header,
                 language: Language):
        self.__partial_sheets_created = False
        self.__partial_sheets = {}
        self.__row_to_partial_sheet_map = {}
        self.__partial_sheets_lock = Lock()
        self.__collection = collection
        self.__header = header
        self.__language = language
        self.__t_cls = t_cls

    def __len__(self):
        import operator
        self.__create_all_partial_sheets()
        return sum(map(operator.length_hint, self.__partial_sheets.values()))

    @property
    def keys(self) -> IterableT[int]:
        self.__create_all_partial_sheets()
        return self.__row_to_partial_sheet_map.keys()

    def __iter__(self):
        self.__create_all_partial_sheets()
        for partial in self.__partial_sheets.values():
            for row in partial:
                yield row

    def get_buffer(self):
        raise NotImplementedError

    def _create_partial_sheet(self, _range: range, _file: File) -> ISheet[T]:
        return PartialDataSheet[T](self.__t_cls, self, _range, _file)

    def _get_partial_file(self, _range: range) -> File:
        PARTIAL_FILE_NAME_FORMAT = "exd/%s_%u%s.exd"

        partial_file_name = PARTIAL_FILE_NAME_FORMAT % (self.header.name, _range.start, self.language.get_suffix())
        file = self.collection.pack_collection.get_file(partial_file_name)
        if file is None:
            raise FileNotFoundError(partial_file_name)

        return file

    def _get_partial_sheet(self, row: int) -> ISheet[T]:
        if row in self.__row_to_partial_sheet_map:
            return self.__row_to_partial_sheet_map[row]

        res = [item for item in self.header.data_file_ranges if row in item]
        if not any(res):
            raise ValueError("row")

        with self.__partial_sheets_lock:
            _range = res[0]
            partial = self.__partial_sheets.get(_range)
            if partial is None:
                partial = self.__create_partial_sheet(_range)
            return partial

    def __create_all_partial_sheets(self):
        with self.__partial_sheets_lock:
            if self.__partial_sheets_created:
                return

            for _range in self.header.data_file_ranges:
                if _range in self.__partial_sheets:
                    continue
                self.__create_partial_sheet(_range)

            self.__partial_sheets_created = True

    def __create_partial_sheet(self, _range: range) -> ISheet[T]:
        file = self._get_partial_file(_range)

        partial = self._create_partial_sheet(_range, file)
        self.__partial_sheets[_range] = partial
        for k in partial.keys:
            self.__row_to_partial_sheet_map[k] = partial
        return partial

    def __getitem__(self, item: Union[int, Tuple[int, int]]) -> Union[T, IRow, object]:
        if isinstance(item, tuple):
            row = item[0]  # type: int
            column = item[1]  # type: int
            return (self._get_partial_sheet(row)[row])[column]
        else:
            row = item  # type: int
            return self._get_partial_sheet(row)[row]

    def __contains__(self, row: int):
        self.__create_all_partial_sheets()
        return row in self.__row_to_partial_sheet_map
