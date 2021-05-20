
from typing import Tuple

ByteLengthCutoff = 0xF0


class IntegerType(object):
    Null = 0
    Byte = 0xF0
    _Byte = 0xFF
    ByteTimes256 = 0xF1
    Int16 = 0xF2
    ByteSHL16 = 0xF3
    Int16Packed = 0xF4
    Int16SHL8 = 0xF5
    Int24Special = 0xF6
    Int8SHL24 = 0xF7
    Int8SHL8Int8 = 0xF8
    Int8SHL8Int8SHL8 = 0xF9
    Int24 = 0xFA
    Int16SHL16 = 0xFB
    Int24Packed = 0xFC
    Int16Int8SHL8 = 0xFD
    Int32 = 0xFE


Int16 = lambda raw: (0 | raw[0] << 8 | raw[1], raw[2:])

Int24 = lambda raw: (0 | raw[0] << 16 | raw[1] << 8 | raw[2], raw[3:])

IntegerReader = {
    IntegerType.Byte: lambda raw: (raw[0], raw[1:]),
    # IntegerType._Byte: lambda raw: (raw[0], raw[1:]),
    IntegerType.ByteTimes256: lambda raw: (raw[0] * 256, raw[1:]),
    IntegerType.ByteSHL16: lambda raw: (raw[0] << 16, raw[1:]),
    IntegerType.Int8SHL24: lambda raw: (raw[0] << 24, raw[1:]),
    IntegerType.Int8SHL8Int8: lambda raw: (0 | raw[0] << 24 | raw[1], raw[2:]),
    IntegerType.Int8SHL8Int8SHL8: lambda raw: (0 | raw[0] << 24 | raw[1] << 8, raw[2:]),
    IntegerType.Int16: Int16,
    IntegerType.Int16Packed: Int16,
    IntegerType.Int16SHL8: lambda raw: (0 | raw[0] << 16 | raw[1] << 8, raw[2:]),
    IntegerType.Int16SHL16: lambda raw: (0 | raw[0] << 24 | raw[1] << 16, raw[2:]),
    IntegerType.Int24Special: Int24,
    IntegerType.Int24Packed: Int24,
    IntegerType.Int24: Int24,
    IntegerType.Int16Int8SHL8: lambda raw: (0 | raw[0] << 24 | raw[1] << 16 | raw[2] << 8, raw[3:]),
    IntegerType.Int32: lambda raw: (0 | raw[0] << 24 | raw[1] << 16 | raw[2] << 8 | raw[3], raw[4:])
}


class NotSupportedType(Exception):
    def __init__(self, i_type=None):
        msg="Not Supported Type %s" % hex(i_type) if i_type is not None else "Not Supported Format"
        super(NotSupportedType, self).__init__(msg)


def get_packed_integer(raw_data) -> Tuple[int, int, bytes]:
    i_type = raw_data[0]
    value, remain = get_integer(raw_data)
    if i_type == IntegerType.Int24Packed:
        return (value & 0xFFFF00) >> 8, value & 0xFF, remain
    else:
        if value > 0xffff:
            return (value & 0xFFFF0000) >> 16, value & 0xFFFF, remain
        elif value > 0xff:
            return (value & 0xFF00) >> 8, value & 0xFF, remain
    raise NotSupportedType()


def get_integer(raw_data: bytes) -> Tuple[int, bytes]:
    i_type = raw_data[0]
    if i_type < ByteLengthCutoff:
        return i_type - 1, raw_data[1:]
    if i_type not in IntegerReader:
        raise NotSupportedType(i_type)
    return IntegerReader[i_type](raw_data[1:])
