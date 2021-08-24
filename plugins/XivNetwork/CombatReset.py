from FFxivPythonTrigger import *


class CombatResetEvent(EventBase):
    id = "network/combat_reset"
    name = "network combat reset"


class CombatReset(PluginBase):
    name = "CombatReset"

    def __init__(self):
        super().__init__()
        self.register_event('network/actor_control/director_update/fade_in', self._process)
        self.register_event('network/actor_control/director_update/barrier_up', self._process)
        self.register_event('network/actor_control/unknown_director_update', self.process)

    def _process(self, evt=None):
        process_event(CombatResetEvent())

    def process(self, evt):
        if evt.raw_msg.param2 == 0x40000016:self._process()
