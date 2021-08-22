from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import SendNetworkEventBase

ClientEventFinish = OffsetStruct({
    'event_id': c_ushort,
    'category': c_ushort,
    'unk2': c_uint,
    'unk3': c_uint,
    'unk4': c_uint,
}, 16)

_logger = Logger("XivNetwork/ProcessClientEventFinish")
size = sizeof(ClientEventFinish)


class ClientEventFinishEvent(SendNetworkEventBase):
    id = "network/send_event_finish"
    name = "network send event finish"

    def text(self):
        return f"event finish {self.raw_msg.category}-{self.raw_msg.event_id}"


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ClientEventFinishEvent(msg_time, header, ClientEventFinish.from_buffer(raw_msg))
