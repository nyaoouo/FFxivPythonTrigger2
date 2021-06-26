from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from ..Structs import ServerUpdateHpMpTp, RecvNetworkEventBase

_logger = Logger("XivNetwork/ProcessActorUpdateHpMpTp")
size = sizeof(ServerUpdateHpMpTp)


class RecvActorUpdateHpMpTpEvent(RecvNetworkEventBase):
    id = "network/actor_update_hp_mp_tp"
    name = "network actor update hp mp tp event"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.actor_id = raw_msg.header.actor_id
        self.current_hp = raw_msg.current_hp
        self.current_mp = raw_msg.current_mp

    def text(self):
        return f"{hex(self.actor_id)[2:]} - {self.current_hp},{self.current_mp}"


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return RecvActorUpdateHpMpTpEvent(msg_time, ServerUpdateHpMpTp.from_buffer(raw_msg))
