from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase

_logger = Logger("XivNetwork/ProcessActorCast")

ServerActorCast = OffsetStruct({
    'action_id': c_ushort,
    'skill_type': c_ubyte,
    'unk0': c_ubyte,
    'unk1': c_uint,
    'cast_time': c_float,
    'target_id': c_uint,
    'rotation': c_float,
    'unk2': c_uint,
    'x': c_ushort,
    'y': c_ushort,
    'z': c_ushort,
    'unk3': c_ushort,
})

size = sizeof(ServerActorCast)
_logger.debug("size: %d"%size)

class RecvActorCastEvent(RecvNetworkEventBase):
    id = "network/actor_cast"
    name = "network actor cast event"

    def __init__(self, msg_time,header, raw_msg):
        super().__init__(msg_time,header, raw_msg)
        self.source_id = header.actor_id
        self.target_id = raw_msg.target_id
        self.action_id = raw_msg.action_id
        self.cast_time = raw_msg.cast_time

    def text(self):
        return f"{hex(self.source_id)[2:]} is casting {self.action_id} on {hex(self.target_id)[2:]} on {self.cast_time}s"


def get_event(msg_time: datetime,header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return RecvActorCastEvent(msg_time,header, ServerActorCast.from_buffer(raw_msg))
