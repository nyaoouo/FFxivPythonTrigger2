from ctypes import *
from _ctypes import Array
from typing import Type, List, Tuple, Dict
from . import read_pointer_shift, memory


def get_data(data, full=False):
    if isinstance(data, _OffsetStruct):
        return {k: get_data(v, full) for k, v in (data.get_full_item if full else data.get_item)()}
    if isinstance(data, _EnumStruct):
        return data.value()
    if isinstance(data, Array):
        return [get_data(i, full) for i in data]
    return data


class _OffsetStruct(Structure):
    _pack_ = 1
    raw_fields: Dict[str, Tuple[any, int]] = None

    def get_data(self, full=False):
        return get_data(self, full)

    def __str__(self):
        return str(get_data(self))

    def get_full_item(self):
        for k, _ in self._fields_:
            yield k, getattr(self, k)

    def get_item(self):
        for k in self.raw_fields.keys():
            yield k, getattr(self, k)


def _(res) -> Tuple[any, int]:
    return (res[0], res[1]) if type(res) == tuple else (res, -1)


def pad_unk(current: int, target: int):
    if current % 2 or target - current == 1: return c_ubyte, 1, "byte"
    if current % 4 or target - current < 4: return c_ushort, 2, "ushort"
    return c_uint, 4, "uint"


def OffsetStruct(fields: dict, full_size: int = None) -> Type[_OffsetStruct]:
    set_fields = []
    current_size = 0
    for name, data in sorted(fields.items(), key=lambda x: _(x[1])[1]):
        d_type, offset = _(data)
        if offset < 0: offset = current_size
        if current_size > offset:
            raise Exception("block [%s] is invalid" % name)
        while current_size < offset:
            t, s, n = pad_unk(current_size, offset)
            set_fields.append((f"_{n}_{hex(current_size)}", t))
            current_size += s
        data_size = sizeof(d_type)
        set_fields.append((name, d_type))
        current_size += data_size
    if full_size is not None:
        if full_size < current_size:
            raise Exception("full size is smaller than current size")
        while current_size < full_size:
            t, s, n = pad_unk(current_size, full_size)
            set_fields.append((f"_{n}_{hex(current_size)}", t))
            current_size += s
    return type("OffsetStruct", (_OffsetStruct,), {
        'raw_fields': fields,
        '_fields_': set_fields,
    })


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
    return type("PointerStruct", (_PointerStruct,), {
        'shifts': i_shifts,
        'd_type': i_d_type,
    })


class _EnumStruct(Structure):
    _default:any
    _data: dict
    _reverse: dict

    def value(self):
        try:
            return self._data[self.raw_value]
        except KeyError:
            return self.raw_value if self._default is None else self._default

    def set(self, value):
        try:
            self.raw_value = self._reverse[value]
        except KeyError:
            self.raw_value = value


def EnumStruct(raw_type: any, enum_data: dict, default=None) -> Type[_EnumStruct]:
    return type("EnumStruct", (_EnumStruct,), {
        '_default': default,
        '_data': enum_data,
        '_reverse': {v: k for k, v in enum_data.items()},
        '_fields_': [('raw_value', raw_type)],
    })
