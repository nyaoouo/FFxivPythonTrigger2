from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import SendNetworkEventBase

ClientActionSend = OffsetStruct({
    'action_type': (c_uint, 0x0),
    'action_id': (c_uint, 0x4),
    'cnt': (c_ushort, 0x8),
    '_unk_ushort4': (c_ushort, 0xa),
    '_unk_ushort5': (c_ushort, 0xc),
    '_unk_ushort6': (c_ushort, 0xe),
    'target_id': (c_uint, 0x10),
}, 32)
_logger = Logger("XivNetwork/ProcessClientActionSend")
size = sizeof(ClientActionSend)


class ClientActionSendEvent(SendNetworkEventBase):
    id = "network/send_action"
    name = "network send action"

    def text(self):
        return f"use {self.raw_msg.action_type}-{self.raw_msg.action_id} on {self.raw_msg.target_id}"


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ClientActionSendEvent(msg_time, header, ClientActionSend.from_buffer(raw_msg))
