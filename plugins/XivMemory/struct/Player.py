from .JobGauge import *
from ctypes import *


Player=OffsetStruct({
    'localContentId': (c_ulong, 88),
    'job': (c_byte, 106),
    'str': (c_uint, 356),
    'dex': (c_uint, 360),
    'vit': (c_uint, 364),
    'int': (c_uint, 368),
    'mnd': (c_uint, 372),
    'pie': (c_uint, 376),
    'tenacity': (c_uint, 428),
    'attack': (c_uint, 432),
    'directHit': (c_uint, 440),
    'crit': (c_uint, 460),
    'attackMagicPotency': (c_uint, 484),
    'healMagicPotency': (c_uint, 488),
    'det': (c_uint, 528),
    'skillSpeed': (c_uint, 532),
    'spellSpeed': (c_uint, 536),
    'craft': (c_uint, 632),
    'control': (c_uint, 636),
})
