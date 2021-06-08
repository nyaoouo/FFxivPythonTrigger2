from ctypes import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from .Enum import Jobs

Player = OffsetStruct({  # cn5.45
    'job': (Jobs, 18),
    'str': (c_uint, 268),
    'dex': (c_uint, 272),
    'vit': (c_uint, 276),
    'int': (c_uint, 280),
    'mnd': (c_uint, 284),
    'pie': (c_uint, 288),
    'tenacity': (c_uint, 340),
    'attack': (c_uint, 344),
    'directHit': (c_uint, 352),
    'crit': (c_uint, 372),
    'attackMagicPotency': (c_uint, 396),
    'healMagicPotency': (c_uint, 400),
    'det': (c_uint, 440),
    'skillSpeed': (c_uint, 444),
    'spellSpeed': (c_uint, 448),
    'craft': (c_uint, 544),
    'control': (c_uint, 548),
})

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

