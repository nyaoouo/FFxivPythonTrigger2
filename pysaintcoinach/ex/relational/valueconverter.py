from abc import abstractmethod

from ..datasheet import IDataRow
from .definition import SheetDefinition


class IValueConverter(object):
    @property
    @abstractmethod
    def target_type_name(self) -> str:
        pass

    @property
    @abstractmethod
    def target_type(self) -> type:
        pass

    @abstractmethod
    def convert(self, row: IDataRow, raw_value: object) -> object:
        pass

    @abstractmethod
    def to_json(self) -> 'OrderedDict':
        pass

    @abstractmethod
    def resolve_references(self, sheet_def: SheetDefinition):
        pass
