from ..column import Column
from ... import ex
# import ex.relational
# import ex.relational.definition


class RelationalColumn(Column):
    @property
    def header(self) -> 'ex.relational.RelationalHeader':
        return super(RelationalColumn, self).header

    @property
    def definition(self) -> 'ex.relational.definition.PositionedDataDefinition':
        if self._has_definition:
            return self._definition

        if self.header.sheet_definition is not None:
            definition = self.header.sheet_definition.get_definition(self.index)
            if definition is not None:
                self._definition = definition

        self._has_definition = True
        return self._definition

    @property
    def name(self):
        _def = self.header.sheet_definition
        return _def.get_column_name(self.index) if _def is not None else None

    @property
    def value_type(self) -> str:
        _def = self.header.sheet_definition
        if _def is None:
            return super(RelationalColumn, self).value_type

        t = _def.get_value_type_name(self.index)
        return t or super(RelationalColumn, self).value_type

    def __init__(self, header, index, buffer, offset):
        super(RelationalColumn, self).__init__(header, index, buffer, offset)
        self._has_definition = False
        self._definition = None

    def read(self, buffer: bytes, row: 'ex.datasheet.IDataRow', offset: int = None):
        base_val = super(RelationalColumn, self).read(buffer, row, offset)

        _def = self.definition
        return _def.convert(row, base_val, self.index) if _def is not None else base_val

    def __str__(self):
        return self.name or str(self.index)
