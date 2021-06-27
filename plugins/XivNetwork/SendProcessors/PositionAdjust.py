from ctypes import sizeof
from math import degrees

from FFxivPythonTrigger.Logger import Logger
from ..Structs import SendNetworkEventBase, ClientPositionAdjust

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
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return PositionAdjustEvent(msg_time, ClientPositionAdjust.from_buffer(raw_msg))
