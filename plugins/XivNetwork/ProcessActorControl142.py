from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from .Structs import ServerActorControlCategory, ServerActorControl142,NetworkEventBase

_logger = Logger("XivNetwork/ProcessActorControl142")
_unknown_category = set()
_unknown_dot_hot_type = set()


class EventBase(NetworkEventBase):
    raw_msg: ServerActorControl142
    time: datetime
    target_id: int

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time)


class DotEvent(EventBase):
    id = "network/actor_control/dot"
    name = "network actor dot event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id
        self.buff_id = raw_msg.param1
        self.damage = raw_msg.param3

    def text(self):
        return f"{hex(self.target_id)[2:]} gains {self.damage} damage by debuff:{self.buff_id}"


class HotEvent(DotEvent):
    id = "network/actor_control/hot"
    name = "network actor hot event"

    def text(self):
        return f"{hex(self.target_id)[2:]} gains {self.damage} heal by buff:{self.buff_id}"


class DeathEvent(EventBase):
    id = "network/actor_control/death"
    name = "network actor death"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id
        self.source_id = raw_msg.param1

    def text(self):
        return f"{hex(self.target_id)[2:]} wan defeated by {hex(self.source_id)[2:]}"


class TargetIconEvent(EventBase):
    id = "network/actor_control/target_icon"
    name = "network actor target_icon event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.icon_type = raw_msg.param1
        self.target_id = actor_id

    def text(self):
        return f"{hex(self.target_id)[2:]} wan marked by id:{self.icon_type}"


class EffectUpdateEvent(EventBase):
    id = "network/actor_control/effect_update"
    name = "network actor effect_update event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id
        self.effect_id = raw_msg.param2 & 0xffff
        self.effect_extra = raw_msg.param3 & 0xffff

    def text(self):
        return f"{hex(self.target_id)[2:]} 's effect {self.effect_id} with extra {self.effect_extra} was updated"


class TargetableEvent(EventBase):
    id = "network/actor_control/targetable"
    name = "network actor targetable event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.target_id = actor_id

    def text(self):
        return f"targetable event on {hex(self.target_id)[2:]}"


class TetherEvent(EventBase):
    id = "network/actor_control/tether"
    name = "network actor tether event"

    def __init__(self, raw_msg, msg_time, actor_id):
        super().__init__(raw_msg, msg_time, actor_id)
        self.type = raw_msg.param2
        self.target_id = self.raw_msg.param3
        self.source_id = actor_id

    def text(self):
        return f"{hex(self.target_id)[2:]} was connected to {hex(self.source_id)[2:]} with type {self.type}"


size = sizeof(ServerActorControl142)


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[EventBase]:
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
            if msg.param2 not in _unknown_dot_hot_type:
                _unknown_dot_hot_type.add(msg.param2)
                _logger.debug('unknown dot/hot type: %s' % msg.param2)
    elif msg.category == ServerActorControlCategory.Death:
        return DeathEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.UpdateEffect:
        return EffectUpdateEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.Targetable:
        return TargetableEvent(msg, msg_time, actor_id)
    elif msg.category == ServerActorControlCategory.Tether:
        return
    elif msg.category not in _unknown_category:
        _unknown_category.add(msg.category)
        _logger.debug(f"unknown actor control category: {msg.category} | {hex(msg.param1)} | {hex(msg.param2)} | {hex(msg.param3)} | {hex(msg.param4)}")
