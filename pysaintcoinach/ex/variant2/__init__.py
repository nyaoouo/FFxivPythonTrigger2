from struct import unpack_from
from typing import Iterable as IterableT, TypeVar, Union, Dict

from ..datasheet import DataRowBase, IDataSheet, IDataRow
from ..column import Column
from ..relational import IRelationalDataRow
from ..relational.datasheet import IRelationalDataSheet


class SubRow(DataRowBase, IRelationalDataRow):
    @property
    def parent_row(self): return self.__parent_row

    @property
    def full_key(self): return str(self.parent_row.key) + "." + str(self.key)

    def __init__(self, parent: IDataRow, key: int, offset: int):
        super(SubRow, self).__init__(parent.sheet, key, offset)
        self.__parent_row = parent

    @property
    def sheet(self) -> IRelationalDataSheet:
        return super(SubRow, self).sheet

    @property
    def default_value(self) -> object:
        def_col = self.sheet.header.default_column
        return self[def_col.index] if def_col is not None else None

    def __getitem__(self, item: str) -> object:
        if isinstance(item, int):
            return super(SubRow, self).__getitem__(item)

        col = self.sheet.header.find_column(item)
        if col is None:
            raise KeyError
        return self[col.index]

    def get_raw(self, column_name: Union[str, int] = None, **kwargs) -> object:
        if 'column_index' in kwargs:
            return super(SubRow, self).get_raw(**kwargs)
        if isinstance(column_name, int):
            return super(SubRow, self).get_raw(column_name)

        column = self.sheet.header.find_column(column_name)
        if column is None:
            raise KeyError
        return self.get_raw(column.index)


class DataRow(DataRowBase):
    METADATA_LENGTH = 0x06

    @property
    def length(self): return self.__length

    @property
    def sub_row_count(self): return self.__sub_row_count

    @property
    def sub_row_keys(self) -> IterableT[int]:
        if not self.__is_read:
            self._read()
        return self.__sub_rows.keys()

    @property
    def sub_rows(self) -> IterableT[SubRow]:
        if not self.__is_read:
            self._read()
        return self.__sub_rows.values()

    def get_sub_row(self, key) -> SubRow:
        if not self.__is_read:
            self._read()
        return self.__sub_rows[key]

    def __init__(self, sheet: IDataSheet, key: int, offset: int):
        super(DataRow, self).__init__(sheet, key, offset + self.METADATA_LENGTH)
        self.__is_read = False
        self.__sub_rows = {}  # type: Dict[int, SubRow]

        b = sheet.get_buffer()
        if len(b) < (offset + self.METADATA_LENGTH):
            raise ValueError("Index out of range")

        self.__length, self.__sub_row_count = unpack_from(">lh", b, offset)

    def _read(self):
        self.__sub_rows.clear()

        h = self.sheet.header
        b = self.sheet.get_buffer()
        o = self.offset
        for i in range(self.sub_row_count):
            key, = unpack_from(">h", b, o)
            o += 2

            r = SubRow(self, key, o)
            self.__sub_rows[key] = r

            o += h.fixed_size_data_length

        self.__is_read = True

    def __getitem__(self, item):
        raise RuntimeError('Invalid Operation: Cannot get column on Variant 2 DataRow. Use GetSubRow instead.')

    def get_raw(self, column_index: int, **kwargs):
        raise RuntimeError('Invalid Operation: Cannot get column on Variant 2 DataRow. Use GetSubRow instead.')


class RelationalDataRow(DataRow, IRelationalDataRow):
    @property
    def sheet(self) -> IRelationalDataSheet:
        return super(RelationalDataRow, self).sheet

    def __str__(self):
        def_col = self.sheet.header.default_column
        if def_col is not None:
            return "%s" % self.get_sub_row(def_col.index).default_value
        else:
            return "%s#%u" % (self.sheet.header.name, self.key)

    def __init__(self, sheet: IDataSheet, key: int, offset: int):
        super(RelationalDataRow, self).__init__(sheet, key, offset)

    @property
    def default_value(self) -> object:
        def_col = self.sheet.header.default_column
        return self[def_col.index] if def_col is not None else None

    def __getitem__(self, item: str) -> object:
        if isinstance(item, int):
            return super(RelationalDataRow, self).__getitem__(item)

        col = self.sheet.header.find_column(item)
        if col is None:
            raise KeyError
        return self[col.index]

    def get_raw(self, column_name: Union[str, int] = None, **kwargs) -> object:
        if 'column_index' in kwargs:
            return super(RelationalDataRow, self).get_raw(**kwargs)
        if isinstance(column_name, int):
            return super(RelationalDataRow, self).get_raw(column_name)

        column = self.sheet.header.find_column(column_name)
        if column is None:
            raise KeyError
        return super(RelationalDataRow, self).get_raw(column.index)
