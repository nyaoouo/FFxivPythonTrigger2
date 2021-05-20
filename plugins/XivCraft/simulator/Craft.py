import math
from typing import Union

from FFxivPythonTrigger.SaintCoinach import realm
from . import Manager, Models

lv_dif = dict()
lv_dif_min = 999
lv_dif_max = -999
craft_lv_dif_sheet = realm.game_data.get_sheet('CraftLevelDifference')
for _row in craft_lv_dif_sheet:
    if _row["Difference"] > lv_dif_max:
        lv_dif_max = _row["Difference"]
    if _row["Difference"] < lv_dif_min:
        lv_dif_min = _row["Difference"]
    lv_dif[_row["Difference"]] = (_row["ProgressFactor"] / 100, _row["QualityFactor"] / 100)

clvBase = [120, 260, 390]
clvAdjust = [0, 5, 10, 13, 16, 19, 22, 25, 28, 30]


class CheckUnpass(Exception):
    pass


class CraftData(object):
    def __init__(self, recipe: Models.Recipe, player: Models.Player):
        clv = player.lv if player.lv <= 5 else clvBase[(player.lv - 1) // 10 - 5] + clvAdjust[(player.lv - 1) % 10]
        dif = clv - recipe.rlv
        if dif < lv_dif_min:
            dif = lv_dif_min
        elif dif > lv_dif_max:
            dif = lv_dif_max
        self.progress_lv_dif_factor, self.quality_lv_dif_factor = lv_dif[dif]
        self.base_process = self.progress_lv_dif_factor * (0.21 * player.craft + 2) * (10000 + player.craft) / (10000 + recipe.suggest_craft)
        self.base_quality = list()
        for i in range(11):
            actual_control = math.floor(player.control * (0.2 * i + 1))
            cal_ans = self.quality_lv_dif_factor * (0.35 * actual_control + 35) * (10000 + actual_control) / (10000 + recipe.suggest_control)
            self.base_quality.append(cal_ans)


class Craft(object):
    def __init__(self,
                 recipe: Models.Recipe,
                 player: Models.Player,
                 craft_round: int = 1,
                 current_progress: int = 0,
                 current_quality: int = 0,
                 current_durability: int = None,
                 current_cp: int = None,
                 status: Models.Status = None,
                 effects: dict[str, Models.Effect] = None,
                 craft_data: CraftData = None
                 ):
        self.recipe = recipe
        self.player = player
        self.craft_round = craft_round
        self.current_progress = current_progress
        self.current_quality = current_quality
        self.current_durability = current_durability if current_durability is not None else recipe.max_durability
        self.current_cp = current_cp if current_cp is not None else player.max_cp
        self.status = status if status is not None else Manager.mStatus.DEFAULT_STATUS()
        self.effects = effects if effects is not None else dict()
        self.craft_data = craft_data if craft_data is not None else CraftData(recipe, player)
        self.effect_to_add: dict[str, Models.Effect] = dict()

    def is_finished(self):
        return self.current_progress >= self.recipe.max_difficulty

    def clone(self) -> 'Craft':
        new_effects=dict()
        for e in self.effects.values():
            new_effects[e.name]=e.__class__(e.param)
        return Craft(
            recipe=self.recipe,
            player=self.player,
            craft_round=self.craft_round,
            current_progress=self.current_progress,
            current_quality=self.current_quality,
            current_durability=self.current_durability,
            current_cp=self.current_cp,
            status=self.status,
            effects=new_effects,
            craft_data=self.craft_data,
        )

    def add_effect(self, effect_name: str, param: int):
        new_effect = Manager.effects[effect_name](param)
        if new_effect.name in self.effects:
            del self.effects[new_effect.name]
        self.effect_to_add[new_effect.name] = new_effect

    def merge_effects(self):
        self.effects |= self.effect_to_add
        self.effect_to_add.clear()

    def get_skill_progress(self, skill: Union[Models.Skill, str]) -> int:
        if type(skill) == str:
            skill = Manager.skills[skill]()
        effect_progress = 0
        for e in self.effects.values():
            effect_progress += e.progress_factor(self, skill)
        skill_progress = math.floor(skill.progress(self) * (1 + effect_progress)) / 100
        base_progress_status = math.floor(self.craft_data.base_process * (1 + self.status.progress_factor(self, skill)))
        return math.floor(skill_progress * base_progress_status)

    def get_skill_quality(self, skill: Union[Models.Skill, str]) -> int:
        if "内静" not in self.effects:
            base_quality = self.craft_data.base_quality[0]
        else:
            base_quality = self.craft_data.base_quality[self.effects["内静"].param - 1]
        if type(skill) == str:
            skill = Manager.skills[skill]()
        effect_quality = 0
        for e in self.effects.values():
            effect_quality += e.quality_factor(self, skill)
        skill_quality = math.floor(skill.quality(self) * (1 + effect_quality)) / 100
        base_quality_status = math.floor(base_quality * (1 + self.status.quality_factor(self, skill)))
        return math.floor(skill_quality * base_quality_status)

    def get_skill_durability(self, skill: Union[Models.Skill, str]) -> int:
        if type(skill) == str:
            skill = Manager.skills[skill]()
        effect_durability = 1
        for e in self.effects.values():
            effect_durability *= 1 + e.durability_factor(self, skill)
        return math.ceil(skill.durability(self) * effect_durability * (1 + self.status.durability_factor(self, skill)))

    def get_skill_cost(self, skill: Union[Models.Skill, str]) -> int:
        if type(skill) == str:
            skill = Manager.skills[skill]()
        effect_cost = 1
        for e in self.effects.values():
            effect_cost *= 1 + e.cost_factor(self, skill)
        return math.ceil(skill.cost(self) * effect_cost * (1 + self.status.cost_factor(self, skill)))

    def use_skill(self, skill: Union[Models.Skill, str], check_mode=False) -> 'Craft':
        if type(skill) == str:
            skill = Manager.skills[skill]()

        self.effect_to_add.clear()

        added_progress = self.get_skill_progress(skill)
        added_quality = self.get_skill_quality(skill)
        used_durability = self.get_skill_durability(skill)
        used_cp = self.get_skill_cost(skill)

        if check_mode:
            if self.current_progress + added_progress < self.recipe.max_difficulty and self.current_durability <= used_durability: raise CheckUnpass(skill.name)
            if self.current_cp < used_cp: raise CheckUnpass(skill.name)

        self.current_progress = min(self.current_progress + added_progress, self.recipe.max_difficulty)
        self.current_quality = min(self.current_quality + added_quality, self.recipe.max_quality)
        self.current_durability = self.current_durability - used_durability
        self.current_cp = self.current_cp - used_cp

        skill.after_use(self)

        if skill.pass_rounds:
            self.craft_round += 1
            for e in list(self.effects.values()):
                e.after_round(self, skill)
        self.merge_effects()
        return self

    def simple_str(self):
        return f"{self.recipe}{self.player}:{self.current_progress}/{self.current_quality}/{self.current_durability}/{self.current_cp}"

    def __str__(self):
        return """********** round {round} **********
player:\t{player}
recipe:\t{recipe}
progress:\t{current_progress}/{max_difficulty}
quality:\t{current_quality}/{max_quality}
durability:\t{current_durability}/{max_durability}
CP:\t{current_cp}/{max_cp}
effects:\t{effects}
status:\t{status}
******************************""".format(
            round=self.craft_round,
            recipe=self.recipe,
            player=self.player,
            current_progress=self.current_progress,
            max_difficulty=self.recipe.max_difficulty,
            current_quality=self.current_quality,
            max_quality=self.recipe.max_quality,
            current_durability=self.current_durability,
            max_durability=self.recipe.max_durability,
            current_cp=self.current_cp,
            max_cp=self.player.max_cp,
            effects=" ".join(map(str, self.effects.values())),
            status=self.status,
        )
