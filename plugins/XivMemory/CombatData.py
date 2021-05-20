from FFxivPythonTrigger.memory import *
from FFxivPythonTrigger.memory.StructFactory import PointerStruct
from .struct import Combat
from . import AddressManager

Enemies = PointerStruct(Combat.Enemies, *AddressManager.enemies_shifts)


class CombatData(object):
    combo_state: Combat.ComboState = read_memory(Combat.ComboState, AddressManager.combo_state_addr)
    skill_queue: Combat.SkillQueue = read_memory(Combat.SkillQueue, AddressManager.skill_queue_addr)
    cool_down_group: Combat.CoolDownGroups = read_memory(Combat.CoolDownGroups, AddressManager.cool_down_group_addr)
    _enemies: Enemies = read_memory(Enemies, AddressManager.enemies_base_addr)

    @property
    def skill_ani_lock(self):
        return read_memory(c_float, AddressManager.skill_ani_lock_addr)

    @skill_ani_lock.setter
    def skill_ani_lock(self, value):
        write_float(AddressManager.skill_ani_lock_addr, float(value))

    @property
    def enemies(self) -> Combat.Enemies:
        return self._enemies.value

    @property
    def is_in_fight(self) -> bool:
        return read_memory(c_bool, AddressManager.is_in_fight_addr)


combat_data = CombatData()
