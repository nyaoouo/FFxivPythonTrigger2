from ctypes import *
from math import degrees

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import SendNetworkEventBase, header_size, Vector3

ClientPositionSet = OffsetStruct({
    'r': (c_float, 0),
    'unk0': (c_ushort, 0x4),
    'unk1': (c_ushort, 0x6),
    'pos': (Vector3, 0x8),
    'unk2': (c_uint, 0x14),
}, 24)

_logger = Logger("XivNetwork/ProcessClientPositionSet")
size = sizeof(ClientPositionSet)


class PositionSetEvent(SendNetworkEventBase):
    id = "network/position_set"
    name = "network send self position set"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.new_r = raw_msg.r
        self.new_pos = raw_msg.pos

    def text(self):
        return "move to ({:.2F},{:.2F},{:.2F}) facing {:.2F}°".format(self.new_pos.x, self.new_pos.y, self.new_pos.z, degrees(self.new_r))


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return PositionSetEvent(msg_time, ClientPositionSet.from_buffer(raw_msg[header_size:]))
