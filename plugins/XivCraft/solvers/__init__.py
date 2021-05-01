from FFxivPythonTrigger.Logger import Logger
from plugins.XivCraft.simulator import Models, Craft


class Solver(object):
    recipe: Models.Recipe
    player: Models.Player
    logger: Logger

    def __init__(self, recipe: Models.Recipe, player: Models.Player, logger: Logger):
        self.recipe = recipe
        self.player = player
        self.logger = logger

    @staticmethod
    def suitable(recipe: Models.Recipe, player: Models.Player)->bool:
        return True

    def process(self, craft: Craft.Craft = None, used_skill: Models.Skill = None)->str:
        return "观察"
