from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ctypes import *
# from FFxivPythonTrigger.lumina import lumina
# from Lumina.Excel.GeneratedSheets import Action
#
# action_sheet = lumina.GetExcelSheet[Action]()

from FFxivPythonTrigger.SaintCoinach import realm
action_sheet = realm.game_data.get_sheet('Action')

ComboState = OffsetStruct({
    'remain': (c_float, 0),
    'action_id': (c_uint, 4),
})


class CoolDownGroup(OffsetStruct({
    'duration': (c_float, 8),
    'total': (c_float, 12),
}, 0x14)):
    @property
    def remain(self):
        return self.total - self.duration


class CoolDownGroups(CoolDownGroup * 100):

    def by_skill(self, skill_id: int):
        return self[action_sheet[skill_id]['CooldownGroup']]

    @property
    def gcd_group(self):
        return self[58]

    @property
    def item_group(self):
        return self[59]


Enemy = OffsetStruct({
    'id': (c_uint, 0),
    'can_select': (c_uint, 4),
    'hp_percent': (c_int, 8),
    'cast_percent': (c_int, 16),
})


class SkillQueue(OffsetStruct({
    'mark1': (c_ulong, 0),
    'mark2': (c_ulong, 4),
    'ability_id': (c_ulong, 8),
    'target_id': (c_ulong, 16),
})):
    @property
    def has_skill(self):
        return bool(self.mark1)

    def use_skill(self, skill_id, target_id=0xe0000000):
        self.target_id = target_id
        self.ability_id = skill_id
        self.mark1 = 1
        self.mark2 = 1


class Enemies(Enemy * 8):
    def get_item(self):
        for enemy in self:
            if enemy.id != 0xe0000000:
                yield enemy

    def get_ids(self):
        for enemy in self:
            if enemy.id != 0xe0000000:
                yield enemy.id
