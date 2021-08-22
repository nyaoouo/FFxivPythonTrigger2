from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase

ServerStatusEffectListEntry = OffsetStruct({
    'effect_id': c_ushort,
    'param': c_ushort,
    'duration': c_float,
    'actor_id': c_uint,
})

ServerStatusEffectList = OffsetStruct({
    'job_id': c_ubyte,
    'level_1': c_ubyte,
    'level_2': c_ubyte,
    'level_3': c_ubyte,
    'current_hp': c_uint,
    'max_hp': c_uint,
    'current_mp': c_ushort,
    'max_mp': c_ushort,
    'unk0': c_ushort,
    'damage_shield': c_ubyte,
    'unk1': c_ubyte,
    'effects': ServerStatusEffectListEntry * 30,
})

ServerStatusEffectList2 = OffsetStruct({
    'unk0': c_uint,
    'job_id': c_ubyte,
    'level_1': c_ubyte,
    'level_2': c_ubyte,
    'level_3': c_ubyte,
    'current_hp': c_uint,
    'max_hp': c_uint,
    'current_mp': c_ushort,
    'max_mp': c_ushort,
    'unk1': c_ushort,
    'damage_shield': c_ubyte,
    'unk2': c_ubyte,
    'effects': ServerStatusEffectListEntry * 30,
})

ServerBossStatusEffectList = OffsetStruct({
    'effects_2': ServerStatusEffectListEntry * 30,
    'job_id': c_ubyte,
    'level_1': c_ubyte,
    'level_2': c_ubyte,
    'level_3': c_ubyte,
    'current_hp': c_uint,
    'max_hp': c_uint,
    'current_mp': c_ushort,
    'max_mp': c_ushort,
    'unk0': c_ushort,
    'damage_shield': c_ubyte,
    'unk1': c_ubyte,
    'effects_1': ServerStatusEffectListEntry * 30,
    'unk2': c_uint,
})

_logger = Logger("XivNetwork/ProcessStatusEffectListEffect")
size = sizeof(ServerStatusEffectList)
size2 = sizeof(ServerStatusEffectList2)
sizeB = sizeof(ServerBossStatusEffectList)


class RecvStatusEffectListEvent(RecvNetworkEventBase):
    id = "network/status_effect_list"
    name = "network status effect list event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.actor_id = header.actor_id
        self.current_hp = raw_msg.current_hp
        self.max_hp = raw_msg.max_hp
        self.current_mp = raw_msg.current_mp
        self.max_mp = raw_msg.max_mp
        self.damage_shield = raw_msg.damage_shield
        self.levels = (raw_msg.level_1, raw_msg.level_2, raw_msg.level_3)
        self.effects = [e for e in raw_msg.effects if e.effect_id]

    def text(self):
        e_s = ','.join([f'{e.effect_id}({e.actor_id}:x):{e.duration:.1f}' for e in self.effects if e.effect_id])
        return f"update {self.actor_id:x};{self.current_hp:,}(+{self.damage_shield}%)/{self.max_hp:,};{self.current_mp:,}/{self.max_mp:,};{e_s}"


class RecvBossStatusEffectListEvent(RecvStatusEffectListEvent):
    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.effects += [e for e in raw_msg.effects2 if e.effect_id]


def get_event(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse as status list:[%s]" % raw_msg.hex())
        return
    return RecvStatusEffectListEvent(msg_time, header, ServerStatusEffectList.from_buffer(raw_msg))


def get_event2(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size2:
        _logger.warning("message is too short to parse as status list 2:[%s]" % raw_msg.hex())
        return
    return RecvStatusEffectListEvent(msg_time, header, ServerStatusEffectList2.from_buffer(raw_msg))


def get_eventB(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < sizeB:
        _logger.warning("message is too short to parse as boss status list:[%s]" % raw_msg.hex())
        return
    return RecvStatusEffectListEvent(msg_time, header, ServerBossStatusEffectList.from_buffer(raw_msg))
