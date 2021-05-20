import math
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
            [White, Blue, Red, Green, DeepBlue, Purple, ],
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
    elif craft.recipe.status_flag == 0b1110011:  # 23
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


def SolverTest(recipe: Recipe, player: Player, solver: Type[Solver], rounds: int, log_lv=3, **kwargs):
    craft = Craft(recipe, player)
    output_path = _storage.path / f'data_{int(time())}.txt'
    records = list()

    for i in range(rounds):
        if log_lv > 2: _logger(f"Start testing round #{i + 1}")
        t_craft = craft.clone()
        t_solver = solver(t_craft, _logger, **kwargs)
        t_c_time = 0
        t_s_time = 0
        history = list()
        prev_skill = None
        case = "finish"
        while not t_craft.is_finished():
            c_start = perf_counter()
            t_stats = t_craft.status
            next_skill = t_solver.process(t_craft, prev_skill)
            c_time = perf_counter() - c_start
            if next_skill == "terminate" or next_skill == "":
                case = next_skill if next_skill else "end"
                break
            s_time = skill_time_cal(next_skill)
            prev_skill = use_skill(t_craft, next_skill)
            t_c_time += c_time
            t_s_time += s_time
            history.append([t_stats.name, prev_skill, c_time, s_time])
        score = math.floor(calc_score(t_craft))
        if log_lv > 1: _logger("Round #{} finished {} with quality {} ({})\n In {:2f}s calc time and {:2f}s skill time".format(
            i + 1,
            'success' if t_craft.is_finished() else 'fail',
            t_craft.current_quality,
            score,
            t_c_time,
            t_s_time
        ))
        records.append(
            [t_craft.is_finished() and score > 0, [t_craft.current_cp + t_craft.current_durability * 2, t_craft.current_quality], score, t_c_time,
             t_s_time, case])
        if log_lv > 0:
            with open(output_path, 'a+') as f:
                f.write(dumps(history) + "\n")
    success = 0
    total_score = 0
    total_skill_time = 0
    total_calc_time = 0
    for r in records:
        if r[0]: success += 1
        total_score += r[2]
        total_calc_time += r[3]
        total_skill_time += r[4]
    d = [r[1] + [r[2]] for r in records if r[-1] != 'terminate']
    if log_lv > 0: _logger(f"Finished testing, {success} test pass in {rounds} with qualties:\n"
                           f"{sorted(d, key=lambda x: x[-1], reverse=True)}\n"
                           f"total used calc time: {total_calc_time}s | total skill time: {total_skill_time}s\n"
                           f"Excepted score per hour:{total_score / (total_calc_time + total_skill_time) * 3600}")
    return d
