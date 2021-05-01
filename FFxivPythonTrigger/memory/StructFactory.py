from ctypes import *
from _ctypes import Array
from typing import Type, List, Tuple, Dict
from . import read_pointer_shift, memory


def get_data(data):
    if isinstance(data, _OffsetStruct):
        return {k: get_data(v) for k, v in data.get_item()}
    if isinstance(data, Array):
        return [get_data(i) for i in data]
    return data


class _OffsetStruct(Structure):
    raw_fields: Dict[str, Tuple[any, int]] = None

    def get_data(self):
        return get_data(self)

    def __str__(self):
        return str(get_data(self))

    def get_item(self):
        for k in self.raw_fields.keys():
            yield k, getattr(self, k)


def _(res) -> Tuple[any, int]:
    return (res[0], res[1]) if type(res) == tuple else (res, -1)


def OffsetStruct(fields: dict, full_size: int = None) -> Type[_OffsetStruct]:
    set_fields = []
    current_size = 0
    padding_count = 0
    for name, data in sorted(fields.items(), key=lambda x: _(x[1])[1]):
        d_type, offset = _(data)
        if offset < 0: offset = current_size
        if current_size > offset:
            raise Exception("block [%s] is invalid" % name)
        if current_size < offset:
            pad_size = offset - current_size
            set_fields.append(("_padding_%s" % padding_count, c_byte * pad_size))
            padding_count += 1
            current_size += pad_size
        data_size = sizeof(d_type)
        set_fields.append((name, d_type))
        current_size += data_size
    if full_size is not None:
        if full_size < current_size:
            raise Exception("full size is smaller than current size")
        if full_size > current_size:
            pad_size = full_size - current_size
            set_fields.append(("_padding_%s" % padding_count, c_byte * pad_size))

    class OffsetStruct(_OffsetStruct):
        raw_fields = fields
        _fields_ = set_fields

    return OffsetStruct


class _PointerStruct(c_void_p):
    shifts: List[int] = []
    d_type = c_void_p
    _fields_ = [('base', c_ulonglong)]

    def __getattr__(self, item):
        return getattr(self.value, item)

    @property
    def value(self):
        return memory.read_memory(self.d_type, read_pointer_shift(addressof(self), *self.shifts))


def PointerStruct(i_d_type: any, *i_shifts: int) -> Type[_PointerStruct]:
    class PointerStruct(_PointerStruct):
        shifts = i_shifts
        d_type = i_d_type

    return PointerStruct
