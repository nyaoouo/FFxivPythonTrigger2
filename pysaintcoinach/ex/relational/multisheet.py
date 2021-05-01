from abc import abstractmethod
from typing import TypeVar, Tuple, Type, Union

from ..language import Language
from ..multisheet import IMultiRow, IMultiSheet, MultiRow, MultiSheet
from .datasheet import IRelationalDataRow, RelationalDataSheet
from .sheet import IRelationalRow, IRelationalSheet
from ..sheet import ISheet
from ... import ex
# import ex.relational


class IRelationalMultiRow(IRelationalRow, IMultiRow):
    @property
    @abstractmethod
    def sheet(self) -> 'IRelationalMultiSheet':
        pass

    @abstractmethod
    def __getitem__(self, item: Tuple[str, Language]) -> object:
        pass

    @abstractmethod
    def get_raw(self, column_name: str, language: Language=None) -> object:
        pass


TMulti = TypeVar('TMulti', bound=IRelationalMultiRow)
TData = TypeVar('TData', bound=IRelationalDataRow)


class IRelationalMultiSheet(IMultiSheet[TMulti, TData], IRelationalSheet[TMulti]):
    @property
    @abstractmethod
    def active_sheet(self) -> IRelationalSheet[TData]:
        pass

    @abstractmethod
    def __getitem__(self, item: int) -> TMulti:
        pass

    @abstractmethod
    def get_localised_sheet(self, language: Language) -> IRelationalSheet[TData]:
        pass


class RelationalMultiRow(MultiRow, IRelationalMultiRow):
    def __init__(self, sheet: IMultiSheet, key: int):
        super(RelationalMultiRow, self).__init__(sheet, key)

    @property
    def sheet(self) -> IRelationalMultiSheet:
        return super(RelationalMultiRow, self).sheet

    def __getitem__(self, item):
        if isinstance(item, tuple):
            return self.sheet.get_localised_sheet(item[1])[(self.key, item[0])]
        else:
            return self.sheet.active_sheet[(self.key, item)]

    @property
    def default_value(self) -> object:
        return self.sheet.active_sheet[self.key].default_value

    def get_raw(self, column_name: str, language: Language=None) -> object:
        if language is None:
            return self.sheet.active_sheet[self.key].get_raw(column_name)
        else:
            return self.sheet.get_localised_sheet(language)[self.key].get_raw(column_name)

    def __str__(self):
        def_col = self.sheet.header.default_column
        if def_col is not None:
            return "%s" % self[def_col.index]
        else:
            return "%s#%u" % (self.sheet.header.name, self.key)

    def __repr__(self):
        return str(self)


class RelationalMultiSheet(MultiSheet[TMulti, TData], IRelationalMultiSheet[TMulti, TData]):
    def __init__(self,
                 tmulti_cls: Type[TMulti],
                 tdata_cls: Type[TData],
                 collection: 'ex.relational.RelationalExCollection',
                 header: 'ex.relational.RelationalHeader'):
        super(RelationalMultiSheet, self).__init__(tmulti_cls, tdata_cls, collection, header)
        self.__tmulti_cls = tmulti_cls
        self.__tdata_cls = tdata_cls

    @property
    def collection(self) -> 'ex.relational.RelationalExCollection':
        return super(RelationalMultiSheet, self).collection

    @property
    def header(self) -> 'ex.relational.RelationalHeader':
        return super(RelationalMultiSheet, self).header

    @property
    def active_sheet(self) -> IRelationalSheet[TData]:
        return super(RelationalMultiSheet, self).active_sheet

    def get_localised_sheet(self, language: Language) -> IRelationalSheet[TData]:
        return super(RelationalMultiSheet, self).get_localised_sheet(language)

    def _create_localised_sheet(self, language: Language) -> ISheet[TData]:
        return RelationalDataSheet[TData](self.__tdata_cls, self.collection, self.header, language)

    def __getitem__(self, item: Union[int, Tuple[int, str]]) -> \
            Union[IRelationalRow, object, IRelationalMultiRow]:
        return super(RelationalMultiSheet, self).__getitem__(item)

    def indexed_lookup(self, index: str, key: int) -> IRelationalRow:
        return self.active_sheet.indexed_lookup(index, key)
