from . import Stage1, Stage2, Stage3, Stage4
from .. import Solver

stages = [Stage1.Stage1, Stage2.Stage2, Stage3.Stage3, Stage4.Stage4]


class SkyBuilder23(Solver):
    @staticmethod
    def suitable(craft):
        return craft.recipe.status_flag == 0b1110011

    def __init__(self, craft, logger):
        super().__init__(craft, logger)
        self.stage = 0
        self.process_stages = [s() for s in stages]

    def process(self, craft, used_skill=None) -> str:
        if self.stage < 0: return ''
        if used_skill is None: return '闲静'
        while self.process_stages[self.stage].is_finished(craft, used_skill):
            self.stage += 1
            if self.stage >= len(self.process_stages):
                self.stage = -1
                return ''
        ans = self.process_stages[self.stage].deal(craft, used_skill)
        return ans
