import math
from ctypes import *

from FFxivPythonTrigger.Utils import circle
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

Effect = OffsetStruct({
    'buffId': (c_ushort, 0),
    'param': (c_ushort, 2),
    'timer': (c_float, 4),
    'actorId': (c_uint, 8),
})


class Effects(Effect * 30):
    def get_dict(self, source=None):
        return {effect.buffId: effect for effect in self if effect.buffId and (source is None or effect.actorId == source)}

    def get_items(self, source=None):
        for effect in self:
            if effect.buffId and (source is None or effect.actorId == source):
                yield effect.buffId, effect


Position = OffsetStruct({
    'x': (c_float, 0),
    'z': (c_float, 4),
    'y': (c_float, 8),
    'r': (c_float, 16)
})


class Actor(OffsetStruct({
    'name': (c_char * 68, 48),
    'id': (c_uint, 116),
    'bNpcId': (c_uint, 120),
    'eNpcId': (c_uint, 128),
    'ownerId': (c_uint, 132),
    'type': (c_byte, 140),
    'subType': (c_byte, 141),
    'isFriendly': (c_byte, 142),
    'effectiveDistanceX': (c_byte, 144),
    'playerTargetStatus': (c_byte, 145),
    'effectiveDistanceY': (c_byte, 146),
    'unitStatus1': (c_ubyte, 148),
    'unitStatus2': (c_uint, 260),
    'pos': (Position, 160),
    'pcTargetId': (c_uint, 496),
    'pcTargetId2': (c_uint, 560),
    'npcTargetId': (c_uint, 6136),
    'bNpcNameId': (c_uint, 6328),
    'currentWorldID': (c_ushort, 6460),
    'homeWorldID': (c_ushort, 6462),
    'currentHP': (c_uint, 452),
    'maxHP': (c_uint, 456),
    'currentMP': (c_uint, 460),
    'maxMP': (c_uint, 464),
    'currentGP': (c_ushort, 468),
    'maxGP': (c_ushort, 470),
    'currentCP': (c_ushort, 472),
    'maxCP': (c_ushort, 474),
    'job': (c_byte, 482),
    'level': (c_byte, 483),
    'effects': (Effects, 6616),
    "IsCasting1": (c_bool, 7008),
    "IsCasting2": (c_bool, 7010),
    "CastingID": (c_uint, 7012),
    "CastingTargetID": (c_uint, 7024),
    "CastingProgress": (c_float, 7060),
    "CastingTime": (c_float, 7064),
    'HitboxRadius': (c_float, 192),
    '_status_flags': (c_ubyte, 0x1980),
}, extra_properties=['Name',
                     'can_select',
                     'is_hostile',
                     'is_in_combat',
                     'is_weapon_out',
                     'is_party_member',
                     'is_alliance_member',
                     'is_friend',
                     'is_casting'])):

    def __hash__(self):
        return self.id | self.bNpcId

    def __eq__(self, other):
        if type(other) == Actor:
            return self.id == other.id
        if type(other) == int:
            return self.id == other
        if type(other) == str:
            return self.Name == other

    @property
    def hitbox(self):
        return circle(self.pos.x, self.pos.y, self.HitboxRadius)

    def absolute_distance_xy(self, target: 'Actor'):
        return math.sqrt((self.pos.x - target.pos.x) ** 2 + (self.pos.y - target.pos.y) ** 2)

    def target_radian(self, target: 'Actor'):
        return math.atan2(target.pos.x - self.pos.x, target.pos.y - self.pos.y)

    def target_position(self, target: 'Actor'):
        a = abs(abs(self.target_radian(target) - self.pos.r) - math.pi)
        if a < math.pi / 4:
            return "BACK"
        elif a < math.pi / 4 * 3:
            return "SIDE"
        else:
            return "FRONT"

    @property
    def Name(self):
        return self.name.decode('utf-8', errors='ignore')

    decoded_name = Name

    @property
    def can_select(self):
        a1 = self.unitStatus1
        a2 = self.unitStatus2
        return bool(a1 & 0b10 and a1 & 0b100 and ((a2 >> 11 & 1) <= 0 or a1 >= 128) and not a2 & 0xffffe7f7)

    @property
    def is_hostile(self):
        return bool(self._status_flags & 0b1)

    @property
    def is_in_combat(self):
        return bool(self._status_flags & 0b10)

    @property
    def is_weapon_out(self):
        return bool(self._status_flags & 0b100)

    @property
    def is_party_member(self):
        return bool(self._status_flags & 0b10000)

    @property
    def is_alliance_member(self):
        return bool(self._status_flags & 0b100000)

    @property
    def is_friend(self):
        return bool(self._status_flags & 0b1000000)

    @property
    def is_casting(self):
        return bool(self._status_flags & 0x10000000)

# class ActorTableNode(Structure):
#     _fields_ = [('main_actor', POINTER(Actor)), ('pet_actor', POINTER(Actor))]

# """the above hook is not used because of unknown bug when lots of actor is create/remove"""
#
# _create_logger = Logger("XivMem/ActorCreateHook")
# _remove_logger = Logger("XivMem/ActorRemoveHook")
# _clear_logger = Logger("XivMem/ActorClearHook")
#
#
# class ActorCreateHook(Hook):
#     """
#     (ptr main_actors_ptr , uint unk2, int idx, uint unk4),ptr create_actor_ptr
#
#     cn-5.3.5:+0x7360A0
#     """
#     restype = c_int64
#     argtypes = [c_int64, c_uint, c_int, c_uint]
#     after_callback: callable = None
#
#     def hook_function(self, *args):
#         res = self.original(*args)
#         try:
#             if self.after_callback is not None:
#                 self.after_callback(*args, res)
#         except Exception:
#             _create_logger.warning("error in callback:\n%s" % format_exc())
#         return res
#
#
# class ActorRemoveHook(Hook):
#     """
#     (ptr main_actors_ptr ,int idx)
#
#     cn-5.3.5:+0x7361C9
#     """
#     argtypes = [c_int64, c_int]
#     before_callback: callable = None
#
#     def hook_function(self, *args):
#         try:
#             if self.before_callback is not None:
#                 self.before_callback(*args)
#         except Exception:
#             _remove_logger.warning("error in callback:\n%s" % format_exc())
#         return self.original(*args)
#
#
# class ActorClearHook(Hook):
#     """
#     (ptr main_actors_ptr),int64 unk1
#
#     cn-5.3.5:+0x736260
#     """
#     restype = c_int64
#     argtypes = [c_int64]
#     before_callback: callable = None
#
#     def hook_function(self, *args):
#         try:
#             if self.before_callback is not None:
#                 self.before_callback(*args)
#         except Exception:
#             _clear_logger.warning("error in callback:\n%s" % format_exc())
#         return self.original(*args)
