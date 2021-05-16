from FFxivPythonTrigger.Logger import Logger

from .Opcodes import opcodes
from . import ProcessActorControl142, ProcessActorCast, ProcessAbility
from . import ProcessAddStatusEffect

_logger = Logger("XivNetwork/Processors")

_processors = {
    # 'StatusEffectList': 0x03C1,
    # 'StatusEffectList2': 0xCAFE,
    # 'BossStatusEffectList': 0xCAFE,
    'Ability1': ProcessAbility.get_event1,
    'Ability8': ProcessAbility.get_event8,
    'Ability16': ProcessAbility.get_event16,
    'Ability24': ProcessAbility.get_event24,
    'Ability32': ProcessAbility.get_event32,
    'ActorCast': ProcessActorCast.get_event,
    'AddStatusEffect': ProcessAddStatusEffect.get_event,
    'ActorControl142': ProcessActorControl142.get_event,
    # 'ActorControl143': 0x0078,
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
