from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from .Structs import ServerAddStatusEffect, NetworkEventBase

_logger = Logger("XivNetwork/ProcessAddStatusEffect")
size = sizeof(ServerAddStatusEffect)


class AddStatusEffectEvent(NetworkEventBase):
    id = "network/add_status_effect"
    name = "network add status effect event"

    def __init__(self, raw_msg, msg_time):
        super().__init__(raw_msg, msg_time)
        self.actor_id = raw_msg.header.actor_id
        self.actor_id2 = raw_msg.actor_id
        self.current_hp = raw_msg.current_hp
        self.max_hp = raw_msg.max_hp
        self.current_mp = raw_msg.current_mp
        self.damage_shield = raw_msg.damage_shield
        self.effects = raw_msg.effects[:min(raw_msg.effect_count, 4)]

    def text(self):
        return f"update {hex(self.actor_id)[2:]};{self.current_hp}(+{self.damage_shield}%)/{self.max_hp};{self.current_mp}/10000;{[e.get_data() for e in self.effects]}"


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[NetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return AddStatusEffectEvent(ServerAddStatusEffect.from_buffer(raw_msg), msg_time)
