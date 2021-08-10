from ctypes import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from .Enum import Jobs

Attributes = OffsetStruct({
    'str': (c_uint, 0x4),
    'dex': (c_uint, 0x8),
    'vit': (c_uint, 0xc),
    'int': (c_uint, 0x10),
    'mnd': (c_uint, 0x14),
    'pie': (c_uint, 0x18),
    'tenacity': (c_uint, 0x4c),
    'attack': (c_uint, 0x50),
    'directHit': (c_uint, 0x58),
    'crit': (c_uint, 0x6c),
    'attackMagicPotency': (c_uint, 0x84),
    'healMagicPotency': (c_uint, 0x88),
    'det': (c_uint, 0xb0),
    'skillSpeed': (c_uint, 0xb4),
    'spellSpeed': (c_uint, 0xb8),
    'craft': (c_uint, 0x118),
    'control': (c_uint, 0x11c),
})

Player = OffsetStruct({  # cn5.5
    'id': (c_uint, 0x54),
    'job': (Jobs, 0x6a),
    'jobs_level': (c_ushort * 29, 0x7a),
    'attr': (Attributes, 0x16c),
})

# Player = OffsetStruct({  # cn5.45
#     'job': (Jobs, 18),
#     'str': (c_uint, 268),
#     'dex': (c_uint, 272),
#     'vit': (c_uint, 276),
#     'int': (c_uint, 280),
#     'mnd': (c_uint, 284),
#     'pie': (c_uint, 288),
#     'tenacity': (c_uint, 340),
#     'attack': (c_uint, 344),
#     'directHit': (c_uint, 352),
#     'crit': (c_uint, 372),
#     'attackMagicPotency': (c_uint, 396),
#     'healMagicPotency': (c_uint, 400),
#     'det': (c_uint, 440),
#     'skillSpeed': (c_uint, 444),
#     'spellSpeed': (c_uint, 448),
#     'craft': (c_uint, 544),
#     'control': (c_uint, 548),
# }

# Player = OffsetStruct({
#     'localContentId': (c_ulong, 88),
#     'job': (Jobs, 106),
#     'str': (c_uint, 356),
#     'dex': (c_uint, 360),
#     'vit': (c_uint, 364),
#     'int': (c_uint, 368),
#     'mnd': (c_uint, 372),
#     'pie': (c_uint, 376),
#     'tenacity': (c_uint, 428),
#     'attack': (c_uint, 432),
#     'directHit': (c_uint, 440),
#     'crit': (c_uint, 460),
#     'attackMagicPotency': (c_uint, 484),
#     'healMagicPotency': (c_uint, 488),
#     'det': (c_uint, 528),
#     'skillSpeed': (c_uint, 532),
#     'spellSpeed': (c_uint, 536),
#     'craft': (c_uint, 632),
#     'control': (c_uint, 636),
# })
