import random
from time import time, perf_counter
from typing import Type
from json import dumps

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.Storage import get_module_storage
from .simulator.Craft import Craft
from .simulator.Models import Recipe, Player
from .solvers import Solver
from .simulator.Status import *

_storage = get_module_storage("SkyBuilderTest")
_logger = Logger("SkyBuilderTest")


class CustomRecipe(Recipe):
    def __init__(self, name, rlv, status_flag, suggest_craft, suggest_control, max_difficulty, max_quality, max_durability):
        self.recipe_row = None
        self.name = name
        self.rlv = rlv
        self.status_flag = status_flag
        self.suggest_craft = suggest_craft
        self.suggest_control = suggest_control
        self.max_difficulty = max_difficulty
        self.max_quality = max_quality
        self.max_durability = max_durability


def gen_random_status(craft):
    if craft.recipe.status_flag == 0b111100011:  # 4
        return random.choices(
            [White, Blue, Red, Green, DeepBlue, Purple,],
            [0.3663, 0.1493, 0.1206, 0.12, 0.1205, 0.1233],
        )[0]
    elif craft.recipe.status_flag == 0b1110011:  # 23
        return random.choices(
            [White, Blue, Red, Green, Yellow, ],
            [0.4601, 0.1529, 0.1217, 0.1206, 0.1447],
        )[0]
    else:
        return White


def skill_time_cal(skill):
    if skill in ["设计变动", "精修", "俭约", "崇敬", "阔步", "坚信", "内静", "最终确认", "改革", "秘诀", "观察", "掌握", "长期俭约", ]:
        return 2.6
    else:
        return 1.6


random_skills = {
    "高速制作": 0.5,
    "仓促": 0.6,
    '专心加工': 0.5,
}


def use_skill(craft, skill):
    if skill in random_skills:
        r = random.random()
        if craft.status == "安定":
            r += 0.25
        if r < random_skills[skill]:
            skill += ":fail"
    craft.use_skill(skill)
    craft.status = gen_random_status(craft)()
    return skill


def calc_score(craft):
    Q = craft.current_quality
    Q /= 10
    if craft.recipe.status_flag == 0b111100011:  # 4
        if Q < 5800:
            return 0
        elif Q < 6500:
            return (Q - 5800) / (6500 - 5800) * (370 - 175) + 175
        elif Q < 7700:
            return (Q - 6500) / (7700 - 6500) * (1100 - 370) + 370
        else:
            return (Q - 7700) / (8240 - 7700) * (1262 - 1100) + 1000
    elif craft.recipe.status_flag== 0b1110011:  # 23
        if Q < 5800:
            return 0
        elif Q < 6500:
            return (Q - 5800) / (6500 - 5800) * (370 - 175) + 175
        elif Q < 7400:
            return (Q - 6500) / (7400 - 6500) * (820 - 370) + 370
        else:
            return (Q - 7400) / (8144 - 7400) * (1266 - 820) + 820
    else:
        return 0


def SolverTest(recipe: Recipe, player: Player, solver: Type[Solver], rounds: int):
    craft = Craft(recipe, player)
    output_path = _storage.path / f'data_{int(time())}.txt'
    success = 0
    qualities = list()
    for i in range(rounds):
        _logger(f"Start testing round #{i+1}")
        t_craft = craft.clone()
        t_solver = solver(t_craft, _logger)
        history = list()
        prev_skill = None
        while not t_craft.is_finished():
            c_start = perf_counter()
            t_stats = t_craft.status
            next_skill = t_solver.process(t_craft, prev_skill)
            c_time = perf_counter() - c_start
            if next_skill == "terminate" or next_skill == "":
                break
            s_time = skill_time_cal(next_skill)
            prev_skill = use_skill(t_craft, next_skill)
            history.append([t_stats.name, prev_skill, c_time, s_time])
        if t_craft.is_finished():
            success += 1
            qualities.append(t_craft.current_quality)
        _logger(f"Round #{i+1} finished {'success' if t_craft.is_finished() else 'fail'} with quality {t_craft.current_quality}")
        with open(output_path, 'a+') as f:
            f.write(dumps(history) + "\n")
    qualities.sort(reverse=True)
    _logger(f"Finished testing, {success} test pass in {rounds} with qualties:\n{qualities}")
