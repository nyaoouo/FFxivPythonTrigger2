from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase

ServerUpdateHpMpTp = OffsetStruct({
    'current_hp': c_uint,
    'current_mp': c_ushort,
    'current_tp': c_ushort,
})

_logger = Logger("XivNetwork/ProcessActorUpdateHpMpTp")
size = sizeof(ServerUpdateHpMpTp)


class RecvActorUpdateHpMpTpEvent(RecvNetworkEventBase):
    id = "network/actor_update_hp_mp_tp"
    name = "network actor update hp mp tp event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.actor_id = header.actor_id
        self.current_hp = raw_msg.current_hp
        self.current_mp = raw_msg.current_mp

    def text(self):
        return f"{self.actor_id:x} - {self.current_hp},{self.current_mp}"


def get_event(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
    else:
        return RecvActorUpdateHpMpTpEvent(msg_time, header, ServerUpdateHpMpTp.from_buffer(raw_msg))
