from typing import List, Iterable

from ..header import Header
from .column import RelationalColumn
from ... import ex
# import ex.relational
# import ex.relational.definition

class RelationalHeader(Header):
    @property
    def collection(self) -> 'ex.relational.RelationalExCollection':
        return super(RelationalHeader, self).collection

    @property
    def columns(self) -> Iterable[RelationalColumn]:
        return self.__columns

    @property
    def default_column(self) -> RelationalColumn:
        _def = self.sheet_definition
        if _def is None:
            return None

        i = _def.get_default_column_index()
        return self.get_column(i) if i is not None else None

    @default_column.setter
    def default_column(self, value: RelationalColumn):
        _def = self.get_or_create_sheet_definition()
        _def.default_column = None if value is None else value.name

    @property
    def sheet_definition(self) -> 'ex.relational.definition.SheetDefinition':
        return self.collection.definition.get_sheet(self.name)

    def __init__(self, collection, name, file):
        super(RelationalHeader, self).__init__(collection, name, file)
        self.__columns = super(RelationalHeader, self).columns

    def get_column(self, index: int) -> RelationalColumn:
        return self.__columns[index]

    def get_or_create_sheet_definition(self) -> 'ex.relational.definition.SheetDefinition':
        return self.collection.definition.get_or_create_sheet(self.name)

    def create_column(self, index: int, data: bytes, offset: int) -> RelationalColumn:
        return RelationalColumn(self, index, data, offset)

    def find_column(self, name: str) -> RelationalColumn:
        _def = self.sheet_definition
        if _def is None:
            return None

        i = _def.find_column(name)
        return self.get_column(i) if i is not None else None
