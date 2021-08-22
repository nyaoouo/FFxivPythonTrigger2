from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase


class RecvAddStatusEffectEvent(RecvNetworkEventBase):
    id = "network/add_status_effect"
    name = "network add status effect event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.actor_id = header.actor_id
        self.actor_id2 = raw_msg.actor_id
        self.current_hp = raw_msg.current_hp
        self.max_hp = raw_msg.max_hp
        self.current_mp = raw_msg.current_mp
        self.damage_shield = raw_msg.damage_shield
        self.effects = raw_msg.effects[:min(raw_msg.effect_count, 4)]

    def text(self):
        e_s = ','.join([f'{e.effect_id}({e.source_actor_id}:x):{e.duration:.1f}' for e in self.effects if e.effect_id])
        return f"update {self.actor_id:x};{self.current_hp:,}(+{self.damage_shield}%)/{self.max_hp:,};{self.current_mp:,}/10,000;{e_s}"


ServerStatusEffectAddEntry = OffsetStruct({
    'effect_index': c_ubyte,
    'unk0': c_ubyte,
    'effect_id': c_ushort,
    'unk1': c_ushort,
    'unk2': c_ushort,
    'duration': c_float,
    'source_actor_id': c_uint,
})

ServerAddStatusEffect = OffsetStruct({
    'related_action_sequence': c_uint,
    'actor_id': c_uint,
    'current_hp': c_uint,
    'max_hp': c_uint,
    'current_mp': c_ushort,
    'unk0': c_ushort,
    'damage_shield': c_ubyte,
    'effect_count': c_ubyte,
    'unk1': c_ushort,
    'effects': ServerStatusEffectAddEntry * 4,
    # 'unk2': c_uint,
})

_logger = Logger("XivNetwork/ProcessAddStatusEffect")
size = sizeof(ServerAddStatusEffect)
_logger.debug("size: %d" % size)


def get_event(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return RecvAddStatusEffectEvent(msg_time, header, ServerAddStatusEffect.from_buffer(raw_msg))
