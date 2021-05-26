from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from ..Structs import ServerStatusEffectList, ServerStatusEffectList2, ServerBossStatusEffectList, RecvNetworkEventBase

_logger = Logger("XivNetwork/ProcessStatusEffectListEffect")
size = sizeof(ServerStatusEffectList)
size2 = sizeof(ServerStatusEffectList2)
sizeB = sizeof(ServerBossStatusEffectList)


class RecvStatusEffectListEvent(RecvNetworkEventBase):
    id = "network/status_effect_list"
    name = "network status effect list event"

    def __init__(self, raw_msg, msg_time):
        super().__init__(raw_msg, msg_time)
        self.actor_id = raw_msg.header.actor_id
        self.current_hp = raw_msg.current_hp
        self.max_hp = raw_msg.max_hp
        self.current_mp = raw_msg.current_mp
        self.max_mp = raw_msg.max_mp
        self.damage_shield = raw_msg.damage_shield
        self.levels = (raw_msg.level_1, raw_msg.level_2, raw_msg.level_3)
        self.effects = [e for e in raw_msg.effects if e.effect_id]

    def text(self):
        return f"update {hex(self.actor_id)[2:]};{self.current_hp}(+{self.damage_shield}%)/{self.max_hp};{self.current_mp}/{self.max_mp};{[e.get_data() for e in self.effects]}"


class RecvBossStatusEffectListEvent(RecvStatusEffectListEvent):
    def __init__(self, raw_msg, msg_time):
        super().__init__(raw_msg, msg_time)
        self.effects += [e for e in raw_msg.effects2 if e.effect_id]


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse as status list:[%s]" % raw_msg.hex())
        return
    return RecvStatusEffectListEvent(ServerStatusEffectList.from_buffer(raw_msg), msg_time)


def get_event2(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size2:
        _logger.warning("message is too short to parse as status list 2:[%s]" % raw_msg.hex())
        return
    return RecvStatusEffectListEvent(ServerStatusEffectList2.from_buffer(raw_msg), msg_time)


def get_eventB(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < sizeB:
        _logger.warning("message is too short to parse as boss status list:[%s]" % raw_msg.hex())
        return
    return RecvBossStatusEffectListEvent(ServerBossStatusEffectList.from_buffer(raw_msg), msg_time)
