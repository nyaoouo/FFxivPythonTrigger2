from ctypes import *
from socket import ntohl

from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from FFxivPythonTrigger import EventBase


class NetworkEventBase(EventBase):
    id = "network"
    name = "network event"

    def __init__(self, msg_time, raw_msg):
        self.raw_msg = raw_msg
        self.time = msg_time


class SendNetworkEventBase(NetworkEventBase):
    is_send = True


class RecvNetworkEventBase(NetworkEventBase):
    is_send = False


class Waymark:
    A = 0
    B = 1
    C = 2
    D = 3
    One = 4
    Two = 5
    Three = 6
    For = 7


class ServerActorControlCategory:
    HoT_DoT = 23
    CancelAbility = 15
    Death = 6
    TargetIcon = 34
    Tether = 35
    GainEffect = 20
    LoseEffect = 21
    UpdateEffect = 22
    Targetable = 54
    DirectorUpdate = 109
    SetTargetSign = 502
    LimitBreak = 505
    JobChange = 5
    EffectRemove = 21


class ServerActionEffectDisplayType:
    HideActionName = 0
    ShowActionName = 1
    ShowItemName = 2
    MountName = 13


FFXIVBundleHeader = OffsetStruct({
    'magic0': c_uint,
    'magic1': c_uint,
    'magic2': c_uint,
    'magic3': c_uint,
    'epoch': c_ulonglong,
    'length': c_ushort,
    'unk1': c_ushort,
    'unk2': c_ushort,
    'msg_count': c_ushort,
    'encoding': c_ushort,
    'unk3': c_ushort,
    'unk4': c_ushort,
    'unk5': c_ushort,
})
# @property
# def epoch(self):
#     return (ntohl(self._epoch & 0xFFFFFFFF) << 32) + ntohl(self._epoch >> 32)


ServerMessageHeader = OffsetStruct({
    'msg_length': c_uint,
    'actor_id': c_uint,
    'login_user_id': c_uint,
    'unk1': c_uint,
    'unk2': c_ushort,
    'msg_type': c_ushort,
    'unk3': c_uint,
    'sec': c_uint,
    'unk4': c_uint,
})

header_size = sizeof(ServerMessageHeader)

ServerActionEffectHeader = OffsetStruct({
    'header': ServerMessageHeader,
    'animation_target_id': c_uint,
    'unk1': c_uint,
    'action_id': c_uint,
    'global_effect_counter': c_uint,
    'animation_lock_time': c_float,
    'some_target_id': c_uint,
    'hidden_animation': c_ushort,
    'rotation': c_ushort,
    'action_animation_id': c_ushort,
    'variantion': c_ubyte,
    'effect_display_type': c_ubyte,
    'unk2': c_ubyte,
    'effect_count': c_ubyte,
    'padding': c_ushort,
})

ServerActionEffectEntry = OffsetStruct({
    'type': c_ubyte,
    'param1': c_ubyte,
    'param2': c_ubyte,
    'param3': c_ubyte,
    'param4': c_ubyte,
    'param5': c_ubyte,
    'main_param': c_ushort,
})

ServerActionEffect1 = OffsetStruct({
    'header': ServerActionEffectHeader,
    'padding1': c_uint,
    'padding2': c_ushort,
    'effects': ServerActionEffectEntry * 8 * 1,
    'padding3': c_ushort,
    'padding4': c_uint,
    'target_id': c_ulonglong * 1,
    'padding5': c_uint,
})

ServerActionEffect8 = OffsetStruct({
    'header': ServerActionEffectHeader,
    'padding1': c_uint,
    'padding2': c_ushort,
    'effects': ServerActionEffectEntry * 8 * 8,
    'padding3': c_ushort,
    'padding4': c_uint,
    'target_id': c_ulonglong * 8,
    'effect_flag_1': c_uint,
    'effect_flag_2': c_ushort,
    'padding5': c_ushort,
    'padding6': c_uint,
})

ServerActionEffect16 = OffsetStruct({
    'header': ServerActionEffectHeader,
    'padding1': c_uint,
    'padding2': c_ushort,
    'effects': ServerActionEffectEntry * 8 * 16,
    'padding3': c_ushort,
    'padding4': c_uint,
    'target_id': c_ulonglong * 16,
    'effect_flag_1': c_uint,
    'effect_flag_2': c_ushort,
    'padding5': c_ushort,
    'padding6': c_uint,
})

ServerActionEffect24 = OffsetStruct({
    'header': ServerActionEffectHeader,
    'padding1': c_uint,
    'padding2': c_ushort,
    'effects': ServerActionEffectEntry * 8 * 24,
    'padding3': c_ushort,
    'padding4': c_uint,
    'target_id': c_ulonglong * 24,
    'effect_flag_1': c_uint,
    'effect_flag_2': c_ushort,
    'padding5': c_ushort,
    'padding6': c_uint,
})

ServerActionEffect32 = OffsetStruct({
    'header': ServerActionEffectHeader,
    'padding1': c_uint,
    'padding2': c_ushort,
    'effects': ServerActionEffectEntry * 8 * 32,
    'padding3': c_ushort,
    'padding4': c_uint,
    'target_id': c_ulonglong * 32,
    'effect_flag_1': c_uint,
    'effect_flag_2': c_ushort,
    'padding5': c_ushort,
    'padding6': c_uint,
})

ServerActorCast = OffsetStruct({
    'header': ServerMessageHeader,
    'action_id': c_ushort,
    'skill_type': c_ubyte,
    'unk0': c_ubyte,
    'unk1': c_uint,
    'cast_time': c_float,
    'target_id': c_uint,
    'rotation': c_float,
    'unk2': c_uint,
    'x': c_ushort,
    'y': c_ushort,
    'z': c_ushort,
    'unk3': c_ushort,
})

ServerActorControl142 = OffsetStruct({
    'header': ServerMessageHeader,
    'category': c_ushort,
    'padding0': c_ushort,
    'param1': c_uint,
    'param2': c_uint,
    'param3': c_uint,
    'param4': c_uint,
    'padding1': c_uint,
})

ServerActorControl143 = OffsetStruct({
    'header': ServerMessageHeader,
    'category': c_ushort,
    'padding0': c_ushort,
    'param1': c_uint,
    'param2': c_uint,
    'param3': c_uint,
    'param4': c_uint,
    'param5': c_uint,
    'param6': c_uint,
    'padding1': c_uint,
})

ServerActorControl144 = OffsetStruct({
    'header': ServerMessageHeader,
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

ServerActorGauge = OffsetStruct({
    'header': ServerMessageHeader,
    'buffer': c_ubyte * 16,
})

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
    'header': ServerMessageHeader,
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

ServerPresetWaymark = OffsetStruct({
    'header': ServerMessageHeader,
    'waymark_status': c_uint,
    'x': c_int * 8,
    'z': c_int * 8,
    'y': c_int * 8,
})

ServerStatusEffectListEntry = OffsetStruct({
    'effect_id': c_ushort,
    'param': c_ushort,
    'duration': c_float,
    'actor_id': c_uint,
})

ServerStatusEffectList = OffsetStruct({
    'header': ServerMessageHeader,
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
    'header': ServerMessageHeader,
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
    'header': ServerMessageHeader,
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

ServerUpdateHpMpTp = OffsetStruct({
    'header': ServerMessageHeader,
    'current_hp': c_uint,
    'current_mp': c_ushort,
    'current_tp': c_ushort,
})

ServerWaymark = OffsetStruct({
    'header': ServerMessageHeader,
    'waymark': c_ubyte,
    'status': c_bool,
    'unk0': c_ushort,
    'x': c_int,
    'z': c_int,
    'y': c_int,
})

Vector3 = OffsetStruct({
    'x': c_float,
    'z': c_float,
    'y': c_float,
})

ClientPositionSet = OffsetStruct({
    'header': ServerMessageHeader,
    'r': (c_float, header_size),
    'unk0': (c_ushort, header_size + 0x4),
    'unk1': (c_ushort, header_size + 0x6),
    'pos': (Vector3, header_size + 0x8),
    'unk2': (c_uint, header_size + 0x14),
}, 24 + header_size)

ClientPositionAdjust = OffsetStruct({
    'header': ServerMessageHeader,
    'old_r': (c_float, header_size + 0x0),
    'new_r': (c_float, header_size + 0x4),
    'unk0': (c_ushort, header_size + 0x8),
    'unk1': (c_ushort, header_size + 0xA),
    'old_pos': (Vector3, header_size + 0xC),
    'new_pos': (Vector3, header_size + 0x18),
    'unk2': (c_uint, header_size + 0x24),
}, 40 + header_size)

ClientEventStart = OffsetStruct({
    'header': ServerMessageHeader,
    'target_id': c_uint,
    'unk0': c_uint,
    'event_id': c_ushort,
    'category': c_ushort,
    'unk3': c_uint,
}, 16 + header_size)

ClientEventFinish = OffsetStruct({
    'header': ServerMessageHeader,
    'event_id': c_ushort,
    'category': c_ushort,
    'unk2': c_uint,
    'unk3': c_uint,
    'unk4': c_uint,
}, 16 + header_size)

ClientEventAction = OffsetStruct({
    'header': ServerMessageHeader,
    'event_id': c_ushort,
    'category': c_ushort,
}, 16 + header_size)

ServerEventStart = OffsetStruct({
    'header': ServerMessageHeader,
    'target_id': c_uint,
    'unk0': c_uint,
    'event_id': c_ushort,
    'category': c_ushort,
}, 0x18 + header_size)

ServerEventPlay = OffsetStruct({
    'header': ServerMessageHeader,
    'target_id': c_uint,
    'unk0': c_uint,
    'event_id': c_ushort,
    'category': c_ushort,
}, 0x28 + header_size)

ServerEventFinish = OffsetStruct({
    'header': ServerMessageHeader,
    'event_id': c_ushort,
    'category': c_ushort,
}, 0x10 + header_size)
