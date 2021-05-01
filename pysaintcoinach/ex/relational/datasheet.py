from abc import abstractmethod
from typing import TypeVar, Union, Tuple, Type, Dict, Generic

from ..datasheet import IDataRow, IDataSheet, DataSheet, PartialDataSheet
from .sheet import IRelationalRow, IRelationalSheet
from ..sheet import ISheet
from ...file import File
from ... import ex
from ...util import ConcurrentDictionary
# import ex.relational


T = TypeVar('T', bound=IDataRow)


class RelationalDataIndex(Generic[T]):
    @property
    def source_sheet(self) -> IDataSheet[T]:
        return self.__source_sheet

    @property
    def index_column(self) -> 'ex.Column':
        return self.__index_column

    def __init__(self,
                 t_cls: Type[T],
                 source_sheet: IDataSheet[T],
                 index_column: 'ex.Column'):
        self.__source_sheet = source_sheet
        self.__index_column = index_column
        self.__t_cls = t_cls
        self.__indexed_rows = {}  # type: Dict[int, T]

        self._build_index()

    def _build_index(self):
        self.__indexed_rows = {}
        index = self.index_column.index
        for row in self.source_sheet:
            value = row.get_raw(column_index=index)
            self.__indexed_rows[int(value)] = row

    def __getitem__(self, item: int) -> T:
        return self.__indexed_rows.get(item, None)


class IRelationalDataRow(IRelationalRow, IDataRow):
    @property
    @abstractmethod
    def sheet(self) -> 'IRelationalDataSheet':
        pass

T = TypeVar('T', bound=IRelationalDataRow)


class IRelationalDataSheet(IRelationalSheet[T], IDataSheet[T]):
    @abstractmethod
    def __getitem__(self, item: Union[int, Tuple[int, str]]) -> \
            Union[T, IRelationalRow, object]:
        pass


class RelationalDataSheet(DataSheet[T], IRelationalDataSheet[T]):
    @property
    def collection(self) -> 'ex.relational.RelationalExCollection':
        return super(RelationalDataSheet, self).collection

    @property
    def header(self) -> 'ex.relational.RelationalHeader':
        return super(RelationalDataSheet, self).header

    def __getitem__(self, item):
        return super(RelationalDataSheet, self).__getitem__(item)

    def __init__(self,
                 t_cls: Type[T],
                 collection: 'ex.relational.RelationalExCollection',
                 header: 'ex.relational.RelationalHeader',
                 language: 'ex.Language'):
        super(RelationalDataSheet, self).__init__(t_cls, collection, header, language)
        self.__t_cls = t_cls
        self.__indexes = ConcurrentDictionary()  # type: ConcurrentDictionary[str, RelationalDataIndex[T]]

    def _create_partial_sheet(self, _range: range, _file: File) -> ISheet[T]:
        return RelationalPartialDataSheet[T](self.__t_cls, self, _range, _file)

    def indexed_lookup(self, index_name: str, key: int) -> IRelationalRow:
        if key == 0:
            return None

        def _add_value(i):
            column = self.header.find_column(index_name)
            if column is None:
                raise KeyError()

            return RelationalDataIndex[T](self.__t_cls, self, column)
        index = self.__indexes.get_or_add(index_name, _add_value)
        return index[key]


class RelationalPartialDataSheet(PartialDataSheet[T], IRelationalDataSheet[T]):
    @property
    def source_sheet(self) -> IRelationalDataSheet[T]:
        return super(RelationalPartialDataSheet, self).source_sheet

    @property
    def header(self) -> 'ex.relational.RelationalHeader':
        return super(RelationalPartialDataSheet, self).header

    @property
    def collection(self) -> 'ex.relational.RelationalExCollection':
        return super(RelationalPartialDataSheet, self).collection

    def __getitem__(self, item):
        return super(RelationalPartialDataSheet, self).__getitem__(item)

    def __init__(self,
                 t_cls: Type[T],
                 source_sheet: IRelationalDataSheet[T],
                 _range: range,
                 file: File):
        super(RelationalPartialDataSheet, self).__init__(t_cls,
                                                         source_sheet,
                                                         _range,
                                                         file)

    def indexed_lookup(self, index: str, key: int):
        raise NotImplementedError('Indexes are not supported in partial sheets.')
