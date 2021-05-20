from abc import ABC, abstractmethod
from struct import unpack_from

from ... import ex
from ... import text


class DataReader(ABC):
    @staticmethod
    def get_reader(type):
        return DATA_READERS[type]

    @staticmethod
    def get_field_offset(col: 'ex.column.Column', row: 'ex.datasheet.IDataRow'):
        return col.offset + row.offset

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def length(self) -> int:
        pass

    @property
    @abstractmethod
    def type(self) -> type:
        pass

    @abstractmethod
    def read(self, buffer: bytes, **kwargs):
        pass


class DelegateDataReader(DataReader):
    @property
    def name(self): return self._name

    @property
    def length(self): return self._length

    @property
    def type(self): return self._type

    def __init__(self, name, length, type, func):
        self._name = name
        self._length = length
        self._type = type
        self._func = func

    def read(self, buffer: bytes, **kwargs):
        if 'offset' in kwargs:
            offset = kwargs['offset']
        else:
            offset = self.get_field_offset(kwargs['col'], kwargs['row'])
        return self._func(buffer, offset)


class PackedBooleanDataReader(DataReader):
    @property
    def name(self): return self._name

    @property
    def length(self): return 1

    @property
    def type(self): return type(bool)

    def __init__(self, mask):
        self._mask = mask
        self._name = "bit&%02X" % mask

    def read(self, buffer: bytes, **kwargs):
        if 'offset' in kwargs:
            offset = kwargs['offset']
        else:
            offset = self.get_field_offset(kwargs['col'], kwargs['row'])
        return (buffer[offset] & self._mask) != 0


class StringDataReader(DataReader):
    @property
    def name(self): return "str"

    @property
    def length(self): return 4

    @property
    def type(self): return type(str)

    def read(self, buffer: bytes, **kwargs):
        if 'offset' in kwargs:
            raise NotImplementedError
        field_offset = self.get_field_offset(kwargs['col'], kwargs['row'])
        end_of_fixed = kwargs['row'].offset + kwargs['row'].sheet.header.fixed_size_data_length

        start = end_of_fixed + unpack_from(">l", buffer, field_offset)[0]
        if start < 0:
            return None

        end = buffer.find(b'\0', start)
        # return buffer[start:end].decode()
        return str(text.XivStringDecoder.default().decode(buffer[start:end]))


DATA_READERS = {0x0000: StringDataReader(),
                0x0001: DelegateDataReader("bool", 1, type(bool), lambda d, o: d[o] != 0),
                0x0002: DelegateDataReader("sbyte", 1, type(int), lambda d, o: unpack_from(">b", d, o)[0]),
                0x0003: DelegateDataReader("byte", 1, type(int), lambda d, o: unpack_from(">B", d, o)[0]),
                0x0004: DelegateDataReader("int16", 2, type(int), lambda d, o: unpack_from(">h", d, o)[0]),
                0x0005: DelegateDataReader("uint16", 2, type(int), lambda d, o: unpack_from(">H", d, o)[0]),
                0x0006: DelegateDataReader("int32", 4, type(int), lambda d, o: unpack_from(">l", d, o)[0]),
                0x0007: DelegateDataReader("uint32", 4, type(int), lambda d, o: unpack_from(">L", d, o)[0]),
                0x0009: DelegateDataReader("single", 4, type(float), lambda d, o: unpack_from(">f", d, o)[0]),
                0x000B: DelegateDataReader("int64", 8, type(int), lambda d, o: unpack_from(">q", d, o)[0])}
for i in range(0, 8):
    DATA_READERS[0x19 + i] = PackedBooleanDataReader(1 << i)
