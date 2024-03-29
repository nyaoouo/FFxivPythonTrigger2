from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger import FFxiv_Version

from ..Structs import RecvNetworkEventBase
from .Opcodes import opcodes
from . import AddStatusEffect, Ability, ActorCast, ActorControl142, StatusEffectList, ActorControl143, Ping
from . import ActorControl144, ActorGauge, ActorUpdateHpMpTp, EventStart, EventPlay, EventFinish, CraftStatus
from . import WardLandInfo, ItemInfo, ContainerInfo, CurrencyCrystalInfo, RetainerInformation, UpdateInventorySlot
from . import MarketBoardItemListing, MarketBoardItemListingCount, MarketBoardItemListingHistory

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
    "EventStart": EventStart.get_event,
    "EventFinish": EventFinish.get_event,
    "EventPlay": EventPlay.get_event,
    "CraftStatus": CraftStatus.get_event,
    "WardLandInfo": WardLandInfo.get_event,
    'ItemInfo': ItemInfo.get_event,
    'ContainerInfo': ContainerInfo.get_event,
    'CurrencyCrystalInfo': CurrencyCrystalInfo.get_event,
    'RetainerInformation': RetainerInformation.get_event,
    'UpdateInventorySlot': UpdateInventorySlot.get_event,
    'MarketBoardItemListing': MarketBoardItemListing.get_event,
    'MarketBoardItemListingCount': MarketBoardItemListingCount.get_event,
    'MarketBoardItemListingHistory': MarketBoardItemListingHistory.get_event,
}


class UndefinedRecv(RecvNetworkEventBase):
    def text(self):
        return f"opcode:{self.header.msg_type} len:{len(self.raw_msg)}"


processors = dict()

_undefined_evt_class = dict()
version_opcodes = opcodes.setdefault(FFxiv_Version, dict())

for key, opcode in version_opcodes.items():
    if key not in _processors:
        _logger.debug(f"load recv opcode of [{key}]({hex(opcode)}) - no processor defined")
        processors[opcode] = type(f'RecvUndefined_{key}', (UndefinedRecv,), {
            'id': f"network/undefined_recv/{key}",
            'name': f"network undefined recv - {key}",
        })
    else:
        _logger.debug(f"load recv opcode of [{key}]({hex(opcode)})")
        processors[opcode] = _processors[key]
