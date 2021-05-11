from FFxivPythonTrigger import api
from . import Stage1_s4, Stage1_s23, Stage2_s4, Stage2_s23, Stage3_Bfs, Stage3_Astar,Stage1_s4_v2
from .. import Solver

USE_ASTAR = False


class SkyBuilders(Solver):
    @staticmethod
    def suitable(craft):
        if api.XivMemory.player_info.job!=10:return False
        return craft.recipe.status_flag == 0b1110011 or craft.recipe.status_flag == 0b111100011

    def __init__(self, craft, logger):
        super().__init__(craft, logger)
        self.stage = 0
        if craft.recipe.status_flag == 0b111100011:
            #self_choose_stages = [Stage1_s4.Stage1, Stage2_s4.Stage2]
            self_choose_stages = [Stage1_s4_v2.Stage1]
        else:
            self_choose_stages = [Stage1_s23.Stage1, Stage2_s23.Stage2]
        if USE_ASTAR:
            self_choose_stages += [Stage3_Astar.Stage3, Stage3_Astar.StageEnd]
        else:
            self_choose_stages += [Stage3_Bfs.Stage3, Stage3_Bfs.StageEnd]
        self.process_stages = [s() for s in self_choose_stages]

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
