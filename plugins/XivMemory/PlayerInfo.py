from .struct import Player, JobGauge
from . import AddressManager
from FFxivPythonTrigger.memory import read_memory

gauges = {k: read_memory(v, AddressManager.gauge_addr) for k, v in JobGauge.gauges.items()}


class PlayerInfo(Player.Player):
    @property
    def gauge(self):
        if self.job in gauges:
            return gauges[self.job]


player_info = read_memory(PlayerInfo, AddressManager.player_addr)
