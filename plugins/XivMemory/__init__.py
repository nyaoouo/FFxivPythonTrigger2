import os
from functools import cache

from FFxivPythonTrigger import PluginBase, Logger, memory
from FFxivPythonTrigger.SaintCoinach import realm
from . import ActorTable, CombatData, PlayerInfo, Targets, AddressManager, Movement, Inventory, Party
from . import struct

_logger = Logger.Logger("XivMem")
territory_sheet = realm.game_data.get_sheet('TerritoryType')


@cache
def zone_name(zone_id):
    if not zone_id:return ""
    return territory_sheet[zone_id]['PlaceName']


class XivMemory(object):
    struct = struct
    actor_table = ActorTable.actor_table
    combat_data = CombatData.combat_data
    player_info = PlayerInfo.player_info
    targets = Targets.targets
    movement = Movement.movement
    inventory = Inventory.export
    party = Party.party

    @property
    def zone_id(self):
        return memory.read_uint(AddressManager.zone_addr)

    @property
    def zone_name(self):
        return zone_name(self.zone_id)


class XivMemoryPlugin(PluginBase):
    name = "XivMemory"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/XivMemory'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super(XivMemoryPlugin, self).__init__()
        self.apiClass = XivMemory()
        self.register_api('XivMemory', self.apiClass)
        self.work = False

    def _onunload(self):
        self.work = False
