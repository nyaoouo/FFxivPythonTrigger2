from .. import Solver
from ...simulator.Craft import Craft


class JustDoIt(Solver):
    @staticmethod
    def suitable(recipe, player):
        return player.lv >= 80 and recipe.recipe_row["RecipeLevelTable"]["ClassJobLevel"] + 10 <= player.lv

    def __init__(self, recipe, player, logger):
        super().__init__(recipe, player, logger)
        self.recipe = recipe
        self.player = player
        self.can_hq = recipe.recipe_row["CanHq"]

    def process(self, craft=None, used_skill=None) -> str:
        if craft is None and self.can_hq:
            return '工匠的神速技巧'
        if craft is None:
            craft = Craft(self.recipe,self.player)
        temp = craft.clone().use_skill("坯料制作")
        if temp.is_finished():
            return "坯料制作"
        elif temp.current_durability <= 0:
            return '精修'
        elif '崇敬' in craft.effects:
            return "坯料制作"
        else:
            return '崇敬'
