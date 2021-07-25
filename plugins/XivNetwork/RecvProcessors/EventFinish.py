from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase, header_size

ServerEventFinish = OffsetStruct({
    'event_id': c_ushort,
    'category': c_ushort,
}, 0x10)

_logger = Logger("XivNetwork/ProcessServerEventFinish")
size = sizeof(ServerEventFinish)


class ServerEventFinishEvent(RecvNetworkEventBase):
    id = "network/recv_event_finish"
    name = "network recv event finish"

    def text(self):
        return f"event finish {self.raw_msg.category}-{self.raw_msg.event_id}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerEventFinishEvent(msg_time, ServerEventFinish.from_buffer(raw_msg[header_size:]))
