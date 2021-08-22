from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import SendNetworkEventBase

ClientEventStart = OffsetStruct({
    'target_id': c_uint,
    'unk0': c_uint,
    'event_id': c_ushort,
    'category': c_ushort,
    'unk3': c_uint,
}, 16)

_logger = Logger("XivNetwork/ProcessClientEventStart")
size = sizeof(ClientEventStart)


class ClientEventStartEvent(SendNetworkEventBase):
    id = "network/send_event_start"
    name = "network send event start"

    def text(self):
        return f"event start {self.raw_msg.category}-{self.raw_msg.event_id} (target:{hex(self.raw_msg.target_id)})"


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ClientEventStartEvent(msg_time, header, ClientEventStart.from_buffer(raw_msg))
