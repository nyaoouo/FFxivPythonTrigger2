from ctypes import *
from math import degrees

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import SendNetworkEventBase, header_size, Vector3

ClientPositionAdjust = OffsetStruct({
    'old_r': (c_float, 0x0),
    'new_r': (c_float, 0x4),
    'unk0': (c_ushort, 0x8),
    'unk1': (c_ushort, 0xA),
    'old_pos': (Vector3, 0xC),
    'new_pos': (Vector3, 0x18),
    'unk2': (c_uint, 0x24),
}, 40)

_logger = Logger("XivNetwork/ProcessClientPositionAdjust")
size = sizeof(ClientPositionAdjust)


class PositionAdjustEvent(SendNetworkEventBase):
    id = "network/position_adjust"
    name = "network send self position adjust"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.new_r = raw_msg.new_r
        self.new_pos = raw_msg.new_pos
        self.old_r = raw_msg.old_r
        self.old_pos = raw_msg.old_pos

    def text(self):
        return "from ({:.2F},{:.2F},{:.2F}) facing {:.2F}° adjust to ({:.2F},{:.2F},{:.2F}) facing {:.2F}°".format(
            self.old_pos.x, self.old_pos.y, self.old_pos.z, degrees(self.old_r),
            self.new_pos.x, self.new_pos.y, self.new_pos.z, degrees(self.new_r),
        )


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return PositionAdjustEvent(msg_time, ClientPositionAdjust.from_buffer(raw_msg[header_size:]))
