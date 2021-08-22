from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase


class RecvEventBase(RecvNetworkEventBase):
    raw_msg: 'ServerActorControl142'
    time: datetime
    target_id: int

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)


class DotEvent(RecvEventBase):
    id = "network/actor_control/dot"
    name = "network actor dot event"
    is_dot = True

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.target_id = header.actor_id
        # self.buff_id = raw_msg.param1
        self.damage = raw_msg.param3
        self.source_id = raw_msg.param4
        self.source_buff_id = raw_msg.param1

    def text(self):
        return f"{hex(self.target_id)[2:]} gains {self.damage} damage over time from {self.source_id:x}({self.source_buff_id})"


class HotEvent(DotEvent):
    id = "network/actor_control/hot"
    name = "network actor hot event"
    is_dot = False

    def text(self):
        return f"{hex(self.target_id)[2:]} gains {self.damage} heal over time from {self.source_id:x}({self.source_buff_id})"


class DeathEvent(RecvEventBase):
    id = "network/actor_control/death"
    name = "network actor death"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.target_id = header.actor_id
        self.source_id = raw_msg.param1

    def text(self):
        return f"{hex(self.target_id)[2:]} wan defeated by {hex(self.source_id)[2:]}"


class TargetIconEvent(RecvEventBase):
    id = "network/actor_control/target_icon"
    name = "network actor target_icon event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.icon_type = raw_msg.param1
        self.target_id = header.actor_id

    def text(self):
        return f"{hex(self.target_id)[2:]} wan marked by id:{self.icon_type}"


class EffectUpdateEvent(RecvEventBase):
    id = "network/actor_control/effect_update"
    name = "network actor effect_update event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.target_id = header.actor_id
        self.effect_id = raw_msg.param2 & 0xffff
        self.effect_extra = raw_msg.param3 & 0xffff

    def text(self):
        return f"{hex(self.target_id)[2:]} 's effect {self.effect_id} with extra {self.effect_extra} was updated"


class TargetableEvent(RecvEventBase):
    id = "network/actor_control/targetable"
    name = "network actor targetable event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.target_id = header.actor_id

    def text(self):
        return f"targetable event on {hex(self.target_id)[2:]}"


class TetherEvent(RecvEventBase):
    id = "network/actor_control/tether"
    name = "network actor tether event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.type = raw_msg.param2
        self.target_id = self.raw_msg.param3
        self.source_id = header.actor_id

    def text(self):
        return f"{hex(self.target_id)[2:]} was connected to {hex(self.source_id)[2:]} with type {self.type}"


class JobChangeEvent(RecvEventBase):
    id = "network/actor_control/job_change"
    name = "network job change event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.actor_id = header.actor_id
        self.to_job = raw_msg.param1

    def text(self):
        return f"{hex(self.actor_id)[2:]} change job to {self.to_job}"


class EffectRemoveEvent(RecvEventBase):
    id = "network/actor_control/effect_remove"
    name = "network effect remove event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.target_id = header.actor_id
        self.source_id = raw_msg.param3
        self.effect_id = raw_msg.param1

    def text(self):
        return f"{hex(self.target_id)[2:]} remove effect [{self.effect_id}] from {hex(self.source_id)[2:]}"


class UnknownDotHotEvent(RecvEventBase):
    id = "network/actor_control/unknown_dot_hot"
    name = "network actor unknown dot hot event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.target_id = header.actor_id

    def text(self):
        return f"unknown dot / hot category: {self.raw_msg.param2} | {hex(self.raw_msg.param1)} " \
               f"| {hex(self.raw_msg.param3)} | {hex(self.raw_msg.param4)}"


class UnknownActorControlEvent(RecvEventBase):
    id = "network/actor_control/unknown_actor_control_142"
    name = "network unknown actor control 142 event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.target_id = header.actor_id

    def text(self):
        return f"unknown actor control category: {self.raw_msg.category} | {hex(self.raw_msg.param1)} " \
               f"| {hex(self.raw_msg.param2)} | {hex(self.raw_msg.param3)} | {hex(self.raw_msg.param4)}"


ServerActorControl142 = OffsetStruct({
    'category': c_ushort,
    'padding0': c_ushort,
    'param1': c_uint,
    'param2': c_uint,
    'param3': c_uint,
    'param4': c_uint,
    'padding1': c_uint,
})


def dot_hot_event(msg_time, header, msg):
    return (HotEvent if msg.param2 == 4 else DotEvent if msg.param2 == 3 else UnknownDotHotEvent)(msg_time, header, msg)


size = sizeof(ServerActorControl142)
_logger = Logger("XivNetwork/ProcessActorControl142")
_unknown_category = set()
_unknown_dot_hot_type = set()
_logger.debug("size: %d" % size)

category_event_map = {
    6: DeathEvent,
    22: EffectUpdateEvent,
    54: TargetableEvent,
    35: TetherEvent,
    5: JobChangeEvent,
    21: EffectRemoveEvent,
    23: dot_hot_event,
}


def get_event(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
    else:
        msg = ServerActorControl142.from_buffer(raw_msg)
        return (category_event_map[msg.category] if msg.category in category_event_map else UnknownActorControlEvent)(msg_time, header, msg)

# class ServerActorControlCategory:
#     HoT_DoT = 23
#     CancelAbility = 15
#     Death = 6
#     TargetIcon = 34
#     Tether = 35
#     GainEffect = 20
#     LoseEffect = 21
#     UpdateEffect = 22
#     Targetable = 54
#     DirectorUpdate = 109
#     SetTargetSign = 502
#     LimitBreak = 505
#     JobChange = 5
#     EffectRemove = 21
