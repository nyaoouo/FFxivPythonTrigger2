from ctypes import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

ServerActionEffectHeader = OffsetStruct({
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


class ServerActionEffectDisplayType:
    HideActionName = 0
    ShowActionName = 1
    ShowItemName = 2
    MountName = 13


SWING_TYPES = {
    0x1: {'ability', 'miss'},
    0x2: {'ability'},
    0x3: {'ability'},
    0x4: {'healing'},
    0x5: {'blocked', 'ability'},
    0x6: {'parry', 'ability'},
    0x7: {'invincible'},
    0xA: {'power_drain'},
    0xB: {'power_healing'},
    0xD: {'tp_healing'},
    0xE: {'buff', 'to_target'},
    0xF: {'buff', 'to_source'},
    0x18: {'threat'},
    0x19: {'threat'},
    0x20: {'knock_back'},
    0x21: {'absorb'},
    0x33: {'instant_death'},
    # 0x34: {'buff'},
    0x37: {'buff', 'resistance'},
    0x3D: {'gauge_add'},
}

TYPE_HAVE_AMOUNT = {'ability', 'healing', 'power_drain', 'power_healing''tp_healing'}
TYPE_HAVE_CRITICAL_DIRECT = {'ability', 'healing'}
ABILITY_TYPE = {
    1: {'physics', 'blow'},
    2: {'physics', 'slash'},
    3: {'physics', 'spur'},
    4: {'physics', 'shoot'},
    5: {'magic'},
    6: {'diablo'},
    7: {'sonic'},
    8: {'limit_break'},
}
ABILITY_SUB_TYPE = {
    1: {'fire'},
    2: {'ice'},
    3: {'wind'},
    4: {'ground'},
    5: {'thunder'},
    6: {'water'},
    7: {'unaspected'},
}
