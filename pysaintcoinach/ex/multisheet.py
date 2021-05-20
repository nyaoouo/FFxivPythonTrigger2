from typing import TypeVar, Generic, Tuple, Iterable, Type, Dict
from abc import ABC, abstractmethod
from collections import OrderedDict

from .sheet import IRow, ISheet
from .language import Language
from .header import Header
from .datasheet import DataSheet
from .. import ex
from ..util import ConcurrentDictionary


class IMultiRow(IRow):
    @property
    @abstractmethod
    def sheet(self) -> 'IMultiSheet':
        pass

    @abstractmethod
    def __getitem__(self, item: Tuple[int, Language]) -> object:
        pass

    @abstractmethod
    def get_raw(self, column_index: int, language: Language = None) -> object:
        pass


TMulti = TypeVar('TMulti', bound=IMultiRow)
TData = TypeVar('TData', bound=IRow)


class IMultiSheet(ISheet[TMulti], Generic[TMulti, TData]):
    @property
    @abstractmethod
    def active_sheet(self) -> ISheet[TData]:
        pass

    @abstractmethod
    def __getitem__(self, item: int) -> TMulti:
        pass

    @abstractmethod
    def get_localised_sheet(self, language: Language) -> ISheet[TData]:
        pass


class MultiSheet(IMultiSheet[TMulti, TData]):
    def __init__(self,
                 tmulti_cls: Type[TMulti],
                 tdata_cls: Type[TData],
                 collection: 'ex.ExCollection',
                 header: Header):
        self.__localised_sheets = ConcurrentDictionary()  # type: ConcurrentDictionary[Language, ISheet[TData]]
        self.__rows = ConcurrentDictionary()  # type: ConcurrentDictionary[int, TMulti]
        self.__collection = collection
        self.__header = header
        self.__tmulti_cls = tmulti_cls
        self.__tdata_cls = tdata_cls

    @property
    def collection(self): return self.__collection

    @property
    def header(self): return self.__header

    @property
    def active_sheet(self): return self.get_localised_sheet(self.collection.active_language)

    @property
    def keys(self): return self.active_sheet.keys

    @property
    def name(self): return self.header.name

    def __len__(self):
        return len(self.active_sheet)

    def get_localised_sheet(self, language: Language) -> ISheet[TData]:
        def _add_value(l):
            if l not in self.header.available_languages:
                raise ValueError("language not supported")
            return self._create_localised_sheet(l)

        return self.__localised_sheets.get_or_add(language, _add_value)

    def __iter__(self):
        for key in self.active_sheet.keys:
            yield self[key]

    def _create_multi_row(self, row) -> TMulti:
        return self.__tmulti_cls(self, row)

    def _create_localised_sheet(self, language) -> ISheet[TData]:
        return DataSheet[TData](self.__tdata_cls, self.collection, self.header, language)

    def __getitem__(self, item):
        def get_row(key) -> TMulti:
            return self.__rows.get_or_add(key, lambda k: self._create_multi_row(k))
        if isinstance(item, tuple):
            return get_row(item[0])[item[1]]
        else:
            return get_row(item)

    def __contains__(self, item):
        return item in self.active_sheet


class MultiRow(IMultiRow):
    def __init__(self, sheet: IMultiSheet, key: int):
        self.__sheet = sheet
        self.__key = key

    @property
    def sheet(self): return self.__sheet

    @property
    def key(self): return self.__key

    def __getitem__(self, item):
        if isinstance(item, tuple):
            return self.sheet.get_localised_sheet(item[1])[(self.key, item[0])]
        else:
            return self.sheet.active_sheet[(self.key, item)]

    def get_raw(self, column_index: int, language: Language = None):
        if language is None:
            return self.sheet.active_sheet[self.key].get_raw(column_index)
        else:
            return self.sheet.get_localised_sheet(language)[self.key].get_raw(column_index)

    def column_values(self) -> Iterable[object]:
        return self.sheet.active_sheet[self.key].column_values()

    def items(self):
        item_dict = OrderedDict()
        for c in self.sheet.active_sheet.header.columns:
            item_dict[c.name] = self[c.index]
        return item_dict
