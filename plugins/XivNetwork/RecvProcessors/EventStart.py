from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase, header_size

ServerEventStart = OffsetStruct({
    'target_id': c_uint,
    'unk0': c_uint,
    'event_id': c_ushort,
    'category': c_ushort,
}, 0x18)
_logger = Logger("XivNetwork/ProcessServerEventStart")
size = sizeof(ServerEventStart)


class ServerEventStartEvent(RecvNetworkEventBase):
    id = "network/recv_event_start"
    name = "network recv event start"

    def text(self):
        return f"event start {self.raw_msg.category}-{self.raw_msg.event_id} (target:{hex(self.raw_msg.target_id)})"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerEventStartEvent(msg_time, ServerEventStart.from_buffer(raw_msg, header_size))
