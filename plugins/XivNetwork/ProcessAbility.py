from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from .Structs import ServerActionEffect1, ServerActionEffect8, ServerActionEffect16, ServerMessageHeader
from .Structs import ServerActionEffect24, ServerActionEffect32, ServerActionEffectHeader
from .Structs import ServerActionEffectDisplayType,NetworkEventBase as EventBase

_logger = Logger("XivNetwork/ProcessAbility")

header_size = sizeof(ServerActionEffectHeader)
a1_size = sizeof(ServerActionEffect1)
a8_size = sizeof(ServerActionEffect8)
a16_size = sizeof(ServerActionEffect16)
a24_size = sizeof(ServerActionEffect24)
a32_size = sizeof(ServerActionEffect32)


def get_event1(msg_time: datetime, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a1_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect1 {len(raw_msg)}/{a1_size} [{raw_msg.hex()}]")
    else:
        return get_event(msg_time, ServerActionEffect1.from_buffer(raw_msg), 1)


def get_event8(msg_time: datetime, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a8_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect8 {len(raw_msg)}/{a8_size} [{raw_msg.hex()}]")
    else:
        return get_event(msg_time, ServerActionEffect8.from_buffer(raw_msg), 8)


def get_event16(msg_time: datetime, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a16_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect16 {len(raw_msg)}/{a16_size} [{raw_msg.hex()}]")
    else:
        return get_event(msg_time, ServerActionEffect16.from_buffer(raw_msg), 16)


def get_event24(msg_time: datetime, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a24_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect24 {len(raw_msg)}/{a24_size} [{raw_msg.hex()}]")
    else:
        return get_event(msg_time, ServerActionEffect24.from_buffer(raw_msg), 24)


def get_event32(msg_time: datetime, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a32_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect32 {len(raw_msg)}/{a32_size} [{raw_msg.hex()}]")
    else:
        return get_event(msg_time, ServerActionEffect32.from_buffer(raw_msg), 32)


SWING_TYPES = {
    0x1: {'ability', 'miss'},
    0x2: {'ability'},
    0x3: {'ability'},
    0x4: {'healing'},
    0x5: {'blocked', 'ability'},
    0x6: {'parry', 'ability'},
    0xA: {'power_drain'},
    0xB: {'power_healing'},
    0xD: {'tp_healing'},
    0xE: {'buff'},
    0xF: {'buff'},
    0x18: {'threat'},
    0x19: {'threat'},
    0x33: {'instant_death'},
    0x34: {'buff'},
    0x37: {'buff', 'resistance'},
}

TYPE_HAVE_AMOUNT = {'ability', 'healing', 'power_drain', 'power_healing''tp_healing'}
TYPE_HAVE_CRITICAL_DIRECT = {'ability', 'healing'}
ABILITY_TYPE = {
    1: {'physics', 'blow'},
    2: {'physics', 'slash'},
    3: {'physics', 'spur'},
    5: {'magic'},
    6: {'diablo'},
}


class ActionEffect(object):
    def __init__(self, raw_flag, raw_amount):
        self.raw_flag = raw_flag
        self.raw_amount = raw_amount
        self.tags = set()
        self.param = 0
        self.param2 = 0

        _swing_type = self.raw_flag & 0xff
        if _swing_type in SWING_TYPES:
            self.tags |= SWING_TYPES[_swing_type]
            if self.tags.intersection(TYPE_HAVE_AMOUNT):
                if self.raw_amount >> 8 & 0xff == 0x40:
                    self.param = ((self.raw_amount >> 16) - (self.raw_amount & 0xff)) | ((self.raw_amount & 0xff) << 16)
                else:
                    self.param = self.raw_amount >> 16
                if self.tags.intersection(TYPE_HAVE_CRITICAL_DIRECT):
                    flag = self.raw_flag >> (8 if 'ability' in self.tags else 16) & 0xff
                    if flag & 1: self.tags.add('critical')
                    if flag & 2: self.tags.add('direct')
                if 'ability' in self.tags:
                    flag = self.raw_flag >> 16 & 0xf
                    if flag in ABILITY_TYPE:
                        self.tags |= ABILITY_TYPE[flag]
                    else:
                        self.tags.add(f"ability_type_{flag}")
            elif 'buff' in self.tags:
                self.param = self.raw_amount >> 16
            if self.raw_flag >> 24:
                self.param2 = self.raw_flag >> 24
        else:
            self.tags.add(_swing_type)
            # self.tags.add(hex(self.raw_flag)[2:].zfill(8)+"-"+hex(self.raw_amount)[2:].zfill(8))

    def __str__(self):
        return f"{self.param}{self.tags} "+hex(self.raw_flag)[2:].zfill(8)+"-"+hex(self.raw_amount)[2:]


class ActionEffectEvent(EventBase):
    id = "network/action_effect"
    name = "network action effect"

    def __init__(self, raw_msg, msg_time, actor_id, max_count):
        super().__init__(raw_msg, msg_time)
        self.source_id = actor_id
        header = raw_msg.header
        if header.effect_display_type == ServerActionEffectDisplayType.MountName:
            self.action_type = "mount"
        elif header.effect_display_type == ServerActionEffectDisplayType.ShowItemName:
            self.action_type = "item"
        elif header.effect_display_type == ServerActionEffectDisplayType.ShowActionName or header.effect_display_type == ServerActionEffectDisplayType.HideActionName:
            self.action_type = "action"
        else:
            self.action_type = "unknown_%s" % header.effect_display_type
        self.action_id = header.action_id
        effect_count = min(header.effect_count, max_count)
        self.targets = dict()
        for i in range(effect_count):
            effects = list()
            for j in range(8):
                if not raw_msg.effects[i][j * 2]: break
                effects.append(ActionEffect(raw_msg.effects[i][j * 2], raw_msg.effects[i][j * 2 + 1]))
            self.targets[raw_msg.target_id[i]] = effects

    def text(self):
        m = " / ".join(f"{hex(aid)[2:]}[{' ;'.join(map(str, effects))}]" for aid, effects in self.targets.items())
        return f"{hex(self.source_id)[2:]} use {self.action_id}({self.action_type}) on {len(self.targets)} target(s) : {m}"


def get_event(msg_time: datetime, msg, max_count: int) -> Optional[EventBase]:
    actor_id = msg.header.header.actor_id
    return ActionEffectEvent(msg, msg_time, actor_id, max_count)
