from abc import ABC, abstractmethod
from typing import Union, Tuple, Iterable, TypeVar

from .. import ex


class IRow(ABC):
    @property
    @abstractmethod
    def sheet(self) -> 'ISheet':
        pass

    @property
    @abstractmethod
    def key(self) -> int:
        pass

    @abstractmethod
    def __getitem__(self, column_index: int) -> object:
        pass

    @abstractmethod
    def get_raw(self, column_index: int, **kwargs) -> object:
        pass

    @abstractmethod
    def column_values(self) -> Iterable[object]:
        pass


T = TypeVar('T', bound=IRow)


class ISheet(Iterable[T]):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def header(self) -> 'ex.Header':
        pass

    @property
    @abstractmethod
    def collection(self) -> 'ex.ExCollection':
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __getitem__(self, item: Union[int, Tuple[int, int]]) -> Union[T, IRow, object]:
        """
        Can be used to get a row, or a specific column in a row using a tuple form argument.
        """
        pass

    @property
    @abstractmethod
    def keys(self) -> Iterable[int]:
        pass

    @abstractmethod
    def __contains__(self, row: int):
        pass
