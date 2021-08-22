from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase


class SetTargetEvent(RecvNetworkEventBase):
    id = "network/actor_control/set_target"
    name = "network set target event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.actor_id = raw_msg.param2 if raw_msg.param2 != 0xE0000000 else None
        self.target_id = raw_msg.target_id if raw_msg.target_id != 0xE0000000 else None

    def text(self):
        return f"{hex(self.actor_id)[2:]} set target on {hex(self.target_id)[2:]}"


class UnknownActorControlEvent(RecvNetworkEventBase):
    id = "network/actor_control/unknown_actor_control_144"
    name = "network unknown actor control 144 event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)

    def text(self):
        return f"unknown actor control category: {self.raw_msg.category} | {hex(self.raw_msg.param1)} | {hex(self.raw_msg.param2)} " \
               f"| {hex(self.raw_msg.param3)} | {hex(self.raw_msg.param4)} | {hex(self.raw_msg.target_id)}"


ServerActorControl144 = OffsetStruct({
    'category': c_ushort,
    'padding0': c_ushort,
    'param1': c_uint,
    'param2': c_uint,
    'param3': c_uint,
    'param4': c_uint,
    'padding1': c_uint,
    'target_id': c_uint,
    'padding2': c_uint,
})

_logger = Logger("XivNetwork/ProcessActorControl144")
size = sizeof(ServerActorControl144)
_logger.debug("size: %d" % size)


def get_event(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
    else:
        msg = ServerActorControl144.from_buffer(raw_msg)
        if msg.category == 502:
            return SetTargetEvent(msg_time, header, msg)
        else:
            return UnknownActorControlEvent(msg_time, header, msg)
