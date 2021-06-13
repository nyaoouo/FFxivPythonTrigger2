from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger import FFxiv_Version

from .Opcodes import opcodes
from . import AddStatusEffect, Ability, ActorCast, ActorControl142, StatusEffectList, ActorControl143, Ping
from . import ActorControl144,ActorGauge,ActorUpdateHpMpTp

_logger = Logger("XivNetwork/RecvProcessors")

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
    'ActorControl144': ActorControl144.get_event,
    'UpdateHpMpTp': ActorUpdateHpMpTp.get_event,
    'ActorGauge': ActorGauge.get_event,
    'Ping': Ping.get_event,
}

processors = dict()
_opcodes = opcodes.setdefault(FFxiv_Version,dict())
for k, p in _processors.items():
    if k not in _opcodes:continue
    _logger.debug(f"load opcode of [{k}]({hex(_opcodes[k])})")
    processors[_opcodes[k]] = p
