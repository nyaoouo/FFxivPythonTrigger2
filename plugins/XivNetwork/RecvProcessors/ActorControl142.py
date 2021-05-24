from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from .Structs import ServerActorControlCategory, ServerActorControl142, RecvNetworkEventBase

_logger = Logger("XivNetwork/ProcessActorControl142")
_unknown_category = set()
_unknown_dot_hot_type = set()


class RecvEventBase(RecvNetworkEventBase):
    raw_msg: ServerActorControl142
    time: datetime
    target_id: int

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time)


class DotEvent(RecvEventBase):
    id = "network/actor_control/dot"
    name = "network actor dot event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id
        #self.buff_id = raw_msg.param1
        self.damage = raw_msg.param3

    def text(self):
        return f"{hex(self.target_id)[2:]} gains {self.damage} damage over time"


class HotEvent(DotEvent):
    id = "network/actor_control/hot"
    name = "network actor hot event"

    def text(self):
        return f"{hex(self.target_id)[2:]} gains {self.damage} heal over time"


class DeathEvent(RecvEventBase):
    id = "network/actor_control/death"
    name = "network actor death"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id
        self.source_id = raw_msg.param1

    def text(self):
        return f"{hex(self.target_id)[2:]} wan defeated by {hex(self.source_id)[2:]}"


class TargetIconEvent(RecvEventBase):
    id = "network/actor_control/target_icon"
    name = "network actor target_icon event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.icon_type = raw_msg.param1
        self.target_id = actor_id

    def text(self):
        return f"{hex(self.target_id)[2:]} wan marked by id:{self.icon_type}"


class EffectUpdateEvent(RecvEventBase):
    id = "network/actor_control/effect_update"
    name = "network actor effect_update event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id
        self.effect_id = raw_msg.param2 & 0xffff
        self.effect_extra = raw_msg.param3 & 0xffff

    def text(self):
        return f"{hex(self.target_id)[2:]} 's effect {self.effect_id} with extra {self.effect_extra} was updated"


class TargetableEvent(RecvEventBase):
    id = "network/actor_control/targetable"
    name = "network actor targetable event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id

    def text(self):
        return f"targetable event on {hex(self.target_id)[2:]}"


class TetherEvent(RecvEventBase):
    id = "network/actor_control/tether"
    name = "network actor tether event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.type = raw_msg.param2
        self.target_id = self.raw_msg.param3
        self.source_id = actor_id

    def text(self):
        return f"{hex(self.target_id)[2:]} was connected to {hex(self.source_id)[2:]} with type {self.type}"


class JobChangeEvent(RecvEventBase):
    id = "network/actor_control/job_change"
    name = "network job change event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.actor_id = actor_id
        self.to_job = raw_msg.param1

    def text(self):
        return f"{hex(self.actor_id)[2:]} change job to {self.to_job}"


class EffectRemoveEvent(RecvEventBase):
    id = "network/actor_control/effect_remove"
    name = "network effect remove event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id
        self.source_id = raw_msg.param3
        self.effect_id = raw_msg.param1

    def text(self):
        return f"{hex(self.target_id)[2:]} remove effect [{self.effect_id}] from {hex(self.source_id)[2:]}"


class UnknownDotHotEvent(RecvEventBase):
    id = "network/actor_control/unknown_dot_hot"
    name = "network actor unknown dot hot event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id

    def text(self):
        return f"unknown dot / hot category: {self.raw_msg.param2} | {hex(self.raw_msg.param1)} " \
               f"| {hex(self.raw_msg.param3)} | {hex(self.raw_msg.param4)}"


class UnknownActorControlEvent(RecvEventBase):
    id = "network/actor_control/unknown_actor_control_142"
    name = "network unknown actor control 142 event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id

    def text(self):
        return f"unknown actor control category: {self.raw_msg.category} | {hex(self.raw_msg.param1)} " \
               f"| {hex(self.raw_msg.param2)} | {hex(self.raw_msg.param3)} | {hex(self.raw_msg.param4)}"


size = sizeof(ServerActorControl142)


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    msg = ServerActorControl142.from_buffer(raw_msg)
    actor_id = msg.header.actor_id
    if msg.category == ServerActorControlCategory.HoT_DoT:
        if msg.param2 == 4:
            return HotEvent(msg, msg_time, actor_id)
        elif msg.param2 == 3:
            return DotEvent(msg, msg_time, actor_id)
        else:
            return UnknownDotHotEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.Death:
        return DeathEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.UpdateEffect:
        return EffectUpdateEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.Targetable:
        return TargetableEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.Tether:
        return TetherEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.JobChange:
        return JobChangeEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.EffectRemove:
        return EffectRemoveEvent(msg, msg_time, actor_id)
    else:
        return UnknownActorControlEvent(msg, msg_time, actor_id)
