from abc import abstractmethod
from typing import TypeVar, Union, Tuple

from ..sheet import IRow, ISheet
from ... import ex
# import ex.relational


class IRelationalRow(IRow):
    @property
    @abstractmethod
    def sheet(self) -> 'IRelationalSheet':
        pass

    @property
    @abstractmethod
    def default_value(self) -> object:
        pass

    @abstractmethod
    def __getitem__(self, item: str) -> object:
        pass

    @abstractmethod
    def get_raw(self, column_name: str, **kwargs) -> object:
        pass


T = TypeVar('T', bound=IRelationalRow)


class IRelationalSheet(ISheet[T]):
    @property
    @abstractmethod
    def header(self) -> 'ex.relational.RelationalHeader':
        pass

    @property
    @abstractmethod
    def collection(self) -> 'ex.relational.RelationalExCollection':
        pass

    @abstractmethod
    def __getitem__(self,
                    item: Union[int, Tuple[int, str]]) -> \
            Union[T, IRelationalRow, object]:
        pass

    @abstractmethod
    def indexed_lookup(self, index: str, key: int) -> IRelationalRow:
        pass
