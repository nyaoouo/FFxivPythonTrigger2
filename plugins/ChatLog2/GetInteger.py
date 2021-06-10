from struct import pack
from typing import Tuple

"""
from: https://github.com/goatcorp/Dalamud/blob/master/Dalamud/Game/Text/SeStringHandling/Payload.cs
"""

ByteLengthCutoff2 = 0xD0

r = range(3, -1, -1)


def get_integer(raw_data: bytearray) -> int:
    marker = raw_data.pop(0)
    if marker < ByteLengthCutoff2: return marker - 1
    marker = (marker + 1) & 0b1111
    return int.from_bytes(
        (raw_data.pop(0) if marker & (1 << i) else 0 for i in r),
        byteorder='big'
    )


def make_integer(value: int) -> bytearray:
    if value < ByteLengthCutoff2 - 1:
        return bytearray([value + 1])
    ret = bytearray([0xf0])
    d = pack('I', value)
    for i in r:
        if d[i] != 0:
            ret.append(d[i])
            ret[0] |= 1 << i
    ret[0] -= 1
    return ret


def get_packed_integer(raw_data: bytearray) -> Tuple[int, int]:
    v = get_integer(raw_data)
    return v >> 16, v & 0xffff


def make_packed_integer(high: int, low: int) -> bytearray:
    return make_integer((high << 16) | (low & 0xFFFF))
