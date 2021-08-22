from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase

ServerEventPlay = OffsetStruct({
    'target_id': c_uint,
    'unk0': c_uint,
    'event_id': c_ushort,
    'category': c_ushort,
}, 0x28)

_logger = Logger("XivNetwork/ProcessServerEventPlay")
size = sizeof(ServerEventPlay)


class ServerEventPlayEvent(RecvNetworkEventBase):
    id = "network/recv_event_play"
    name = "network recv event play"

    def text(self):
        return f"event play {self.raw_msg.category}-{self.raw_msg.event_id} (target:{hex(self.raw_msg.target_id)})"


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerEventPlayEvent(msg_time, header, ServerEventPlay.from_buffer(raw_msg))
