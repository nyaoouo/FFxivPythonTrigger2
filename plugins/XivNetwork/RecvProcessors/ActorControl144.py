from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from ..Structs import ServerActorControlCategory, ServerActorControl144, RecvNetworkEventBase

_logger = Logger("XivNetwork/ProcessActorControl144")

size = sizeof(ServerActorControl144)


class SetTargetEvent(RecvNetworkEventBase):
    id = "network/actor_control/set_target"
    name = "network set target event"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.actor_id = raw_msg.param2 if raw_msg.param2 != 0xE0000000 else None
        self.target_id = raw_msg.target_id if raw_msg.target_id != 0xE0000000 else None

    def text(self):
        return f"{hex(self.actor_id)[2:]} set target on {hex(self.target_id)[2:]}"


class UnknownActorControlEvent(RecvNetworkEventBase):
    id = "network/actor_control/unknown_actor_control_144"
    name = "network unknown actor control 144 event"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)

    def text(self):
        return f"unknown actor control category: {self.raw_msg.category} | {hex(self.raw_msg.param1)} | {hex(self.raw_msg.param2)} " \
               f"| {hex(self.raw_msg.param3)} | {hex(self.raw_msg.param4)} | {hex(self.raw_msg.target_id)}"


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    msg = ServerActorControl144.from_buffer(raw_msg)
    if msg.category == ServerActorControlCategory.SetTargetSign:
        return SetTargetEvent(msg_time, msg)
    else:
        return UnknownActorControlEvent(msg_time, msg)
