from FFxivPythonTrigger.Logger import Logger

from plugins.XivNetwork.RecvProcessors.Opcodes import opcodes
from . import AddStatusEffect, Ability, ActorCast, ActorControl142, StatusEffectList, ActorControl143

_logger = Logger("XivNetwork/Processors")

_processors = {
    'StatusEffectList': StatusEffectList.get_event,
    'StatusEffectList2': StatusEffectList.get_event2,
    'BossStatusEffectList': StatusEffectList.get_eventB,
    'Ability1': Ability.get_event1,
    'Ability8': Ability.get_event8,
    'Ability16': Ability.get_event16,
    'Ability24': Ability.get_event24,
    'Ability32': Ability.get_event32,
    'ActorCast': ActorCast.get_event,
    'AddStatusEffect': AddStatusEffect.get_event,
    'ActorControl142': ActorControl142.get_event,
    'ActorControl143': ActorControl143.get_event,
    # 'ActorControl144': 0x02D7,
    # 'UpdateHpMpTp': 0x0262,
    # 'PlayerSpawn': 0x029A,
    # 'NpcSpawn': 0x0313,
    # 'NpcSpawn2': 0xCAFE,
    # 'ActorMove': 0x023B,
    # 'ActorSetPos': 0x026B,
    # 'ActorGauge': 0x039A,
    # 'PresetWaymark': 0x0221,
    # 'Waymark': 0x02B3,
    # 'ActorDrink': 0xCAFE,
}

processors = dict()

for k, p in _processors.items():
    if k not in opcodes: pass
    _logger.debug(f"load opcode of [{k}]({hex(opcodes[k])})")
    processors[opcodes[k]] = p
