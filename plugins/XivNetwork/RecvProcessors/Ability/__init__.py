from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from .Struct import *
from ...Structs import RecvNetworkEventBase as EventBase

_logger = Logger("XivNetwork/ProcessAbility")

a1_size = sizeof(ServerActionEffect1)
a8_size = sizeof(ServerActionEffect8)
a16_size = sizeof(ServerActionEffect16)
a24_size = sizeof(ServerActionEffect24)
a32_size = sizeof(ServerActionEffect32)

_logger.debug(f"a1_size:{a1_size} a8_size:{a8_size} a16_size:{a16_size} a24_size:{a24_size} a32_size:{a32_size} ")


class ActionEffect(object):
    def __init__(self, effect_entry):
        self.raw_entry = effect_entry
        self.tags = set()
        self.param = 0

        if effect_entry.type in SWING_TYPES:
            self.tags = SWING_TYPES[effect_entry.type].copy()
            self.param = effect_entry.main_param
            if self.tags.intersection(TYPE_HAVE_AMOUNT):
                if effect_entry.param5 == 64:
                    self.param += effect_entry.param4 * 65535
                if self.tags.intersection(TYPE_HAVE_CRITICAL_DIRECT):
                    if effect_entry.param1 & 1: self.tags.add('critical')
                    if effect_entry.param1 & 2: self.tags.add('direct')
                if 'ability' in self.tags:
                    main_type = effect_entry.param2 & 0xf
                    self.tags |= ABILITY_TYPE[main_type] if main_type in ABILITY_TYPE else {f"unk_main_type_{effect_entry.param3}"}
                    sub_type = effect_entry.param2 >> 4
                    self.tags |= ABILITY_SUB_TYPE[sub_type] if sub_type in ABILITY_TYPE else {f"unk_sub_type_{effect_entry.param3}"}
        else:
            self.tags.add(f"UnkType_{effect_entry.type}")
            # self.tags.add(hex(self.raw_flag)[2:].zfill(8)+"-"+hex(self.raw_amount)[2:].zfill(8))

    def __str__(self):
        return f"{self.param}{self.tags}" + str(self.raw_entry.get_data())


class RecvActionEffectEvent(EventBase):
    id = "network/action_effect"
    name = "network action effect"

    def __init__(self, msg_time, header, raw_msg, max_count):
        super().__init__(msg_time, header, raw_msg)
        self.source_id = header.actor_id
        effect_header = raw_msg.header
        if effect_header.effect_display_type == ServerActionEffectDisplayType.MountName:
            self.action_type = "mount"
        elif effect_header.effect_display_type == ServerActionEffectDisplayType.ShowItemName:
            self.action_type = "item"
        elif effect_header.effect_display_type == ServerActionEffectDisplayType.ShowActionName or effect_header.effect_display_type == ServerActionEffectDisplayType.HideActionName:
            self.action_type = "action"
        else:
            self.action_type = "unknown_%s" % effect_header.effect_display_type
        self.action_id = effect_header.action_animation_id if self.action_type == "action" else effect_header.action_id
        effect_count = min(effect_header.effect_count, max_count)
        self.targets = dict()
        for i in range(effect_count):
            effects = list()
            for j in range(8):
                if not raw_msg.effects[i][j].type: break
                effects.append(ActionEffect(raw_msg.effects[i][j]))
            self.targets[raw_msg.target_id[i]] = effects

    def text(self):
        m = " / ".join(f"{aid:x}[{' ;'.join(map(str, effects))}]" for aid, effects in self.targets.items())
        return f"{self.source_id:x} use {self.action_id}({self.action_type}) on {len(self.targets)} target(s) : {m}"


def get_event1(msg_time, header, raw_msg) -> Optional[EventBase]:
    if len(raw_msg) < a1_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect1 {len(raw_msg)}/{a1_size} [{raw_msg.hex()}]")
    else:
        return RecvActionEffectEvent(msg_time, header, ServerActionEffect1.from_buffer(raw_msg), 1)


def get_event8(msg_time: datetime, header, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a8_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect8 {len(raw_msg)}/{a8_size} [{raw_msg.hex()}]")
    else:
        return RecvActionEffectEvent(msg_time, header, ServerActionEffect8.from_buffer(raw_msg), 8)


def get_event16(msg_time: datetime, header, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a16_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect16 {len(raw_msg)}/{a16_size} [{raw_msg.hex()}]")
    else:
        return RecvActionEffectEvent(msg_time, header, ServerActionEffect16.from_buffer(raw_msg), 16)


def get_event24(msg_time: datetime, header, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a24_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect24 {len(raw_msg)}/{a24_size} [{raw_msg.hex()}]")
    else:
        return RecvActionEffectEvent(msg_time, header, ServerActionEffect24.from_buffer(raw_msg), 24)


def get_event32(msg_time: datetime, header, raw_msg: bytearray) -> Optional[EventBase]:
    if len(raw_msg) < a32_size:
        _logger.warning(f"message is too short to parse as ServerActionEffect32 {len(raw_msg)}/{a32_size} [{raw_msg.hex()}]")
    else:
        return RecvActionEffectEvent(msg_time, header, ServerActionEffect32.from_buffer(raw_msg), 32)
