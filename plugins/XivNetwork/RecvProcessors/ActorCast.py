from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from ..Structs import ServerActorCast, RecvNetworkEventBase

_logger = Logger("XivNetwork/ProcessActorCast")
size = sizeof(ServerActorCast)


class RecvActorCastEvent(RecvNetworkEventBase):
    id = "network/actor_cast"
    name = "network actor cast event"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.source_id = raw_msg.header.actor_id
        self.target_id = raw_msg.target_id
        self.action_id = raw_msg.action_id
        self.cast_time = raw_msg.cast_time

    def text(self):
        return f"{hex(self.source_id)[2:]} is casting {self.action_id} on {hex(self.target_id)[2:]} on {self.cast_time}s"


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return RecvActorCastEvent(msg_time, ServerActorCast.from_buffer(raw_msg))
