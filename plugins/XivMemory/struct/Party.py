from ctypes import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

Vector3 = OffsetStruct({
    'x': (c_float, 0),
    'z': (c_float, 4),
    'y': (c_float, 8),
})
Effect = OffsetStruct({
    'buffId': (c_ushort, 0),
    'param': (c_ushort, 2),
    'actorId': (c_uint, 8),
})


class Effects(Effect * 30):
    def get_dict(self, source=None):
        return {effect.buffId: effect for effect in self if effect.buffId and (source is None or effect.actorId == source)}

    def get_items(self, source=None):
        for effect in self:
            if effect.buffId and (source is None or effect.actorId == source):
                yield effect.buffId, effect


PartyMember = OffsetStruct({
    "effects": (Effects, 0x8),
    "currentHp": (c_uint, 0x1b4),
    "maxHp": (c_uint, 0x1b8),
    "currentMp": (c_ushort, 0x1bc),
    "maxMp": (c_ushort, 0x1be),
    "pos": (Vector3, 0x190),
    "id": (c_uint, 0x1a8),
    "name": (c_char * 64, 0x1c4),
    "flag": (c_ubyte, 544),
}, full_size=0x230)
