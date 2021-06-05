###############
# tag格式 >> #CraftMacro:[tag]:数据
# 可用配方tag:
# Name: 手法显示名字（默认文件名）
# RecipeID: 适配的配方id，","进行分割
# RecipeName: 适配的物品名字，","进行分割
# MinAttr: 格式"craft/control/max_cp"（默认为0/0/0）
# MaxCraft: 最高作业，避免搓爆（默认-1）
# UsedTime:按照3s普通技能，2s buff计算，作为遍历搜索时的先后排序依据，不填写将不纳入遍历
# StepSafeCheck: 遍历时进行步数测试的最大步数（默认为100步，-1为不测试）
# IgnoreQuality: 遍历匹配时忽略品质，作业推满即可（默认False）
###############
###############
# 配方内可调用关键词（if内使用）
# craft: craft实例
# status: 球色
# prev: 上一个技能名
# effect: 函数，获取buff层数/回合 e.g.effect("內静")
###############

import re
from itertools import chain

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.Storage import get_module_storage
from FFxivPythonTrigger.MacroParser import Macro, MacroFinish
from pathlib import Path

from .. import Solver
from ...simulator.Craft import CheckUnpass

_logger = Logger("CraftMacroSolver")
_storage = get_module_storage("MacroCraft")

macro_dir = Path(__file__).parent / 'macros'
macro_craft_tag_regex = re.compile(r"#CraftMacro:\[(?P<key>[^]]+)]:(?P<arg>[^\n]+)\n")
macro_max_size = 100
macro_pairing = dict()
macros = list()
recipe_pair_id = dict()
recipe_pair_name = dict()
macro_file = "*.macro"


class MacroOversize(Exception):
    pass


class MacroContainer(object):
    def __init__(self, macro_str, file_name):
        self.tags = {gp[0]: gp[1] for gp in macro_craft_tag_regex.findall(macro_str)}
        self.tags['_file'] = file_name
        self.macro = Macro(macro_str)
        self.name = self.tags['Name'] if 'Name' in self.tags else self.tags['_file']
        self.step_safe_check = int(self.tags["StepSafeCheck"]) if "StepSafeCheck" in self.tags else 100
        self.time = int(self.tags["UsedTime"]) if "UsedTime" in self.tags else -1
        self.recipe_id = list(map(int, self.tags["RecipeID"].split(","))) if "RecipeID" in self.tags else []
        self.recipe_name = list(self.tags["RecipeName"].split(",")) if "RecipeName" in self.tags else []
        self.min_craft, self.min_control, self.min_cp = map(int, (self.tags["MinAttr"] if "MinAttr" in self.tags else "0/0/0").split('/'))
        self.max_craft = int(self.tags["MaxCraft"]) if "MaxCraft" in self.tags else -1
        self.ignore_quality = "IgnoreQuality" in self.tags

    def attr_pair(self, player):
        if 0 < self.max_craft < player.craft or player.craft < self.min_craft:
            return False
        if player.control < self.min_control or player.max_cp < self.min_cp:
            return False
        return True

    def pair(self, craft):
        if not self.attr_pair(craft.player):
            return "attr not pair"
        if self.step_safe_check < 0:
            return
        size = 0
        t_craft = craft.clone()
        runner = self.macro.get_runner()
        arg = None
        while True:
            try:
                param = get_params(t_craft, arg)
                cmd, arg, wait_time = runner.next(param)
                while cmd != "ac": cmd, arg, wait = runner.next(param)
                arg = arg.strip('"')
                size += 1
                if size >= self.step_safe_check: raise MacroOversize()
                t_craft.use_skill(arg, check_mode=True)
                if t_craft.is_finished():
                    return None if t_craft.current_quality >= t_craft.recipe.max_quality or self.ignore_quality else "quality not enough"
            except MacroFinish:
                return "craft not finish"
            except MacroOversize:
                return "macro over size"
            except CheckUnpass:
                return "[%s](%s) cant be used" % (arg, runner.current_line - 1)


def get_params(craft, prev):
    return {
        'craft': craft,
        'status': craft.status,
        'prev': prev,
        'effect': lambda name: 0 if name not in craft.effects else craft.effects[name].param,
    }


def load():
    macros.clear()
    macro_pairing.clear()
    recipe_pair_id.clear()
    recipe_pair_name.clear()
    for file in chain(macro_dir.glob(macro_file), _storage.path.glob(macro_file)):
        with open(file, encoding='utf-8') as f:
            macro_str = f.read()
        macro = MacroContainer(macro_str, file.stem)
        if macro.time > 0:
            macros.append(macro)
        for rid in macro.recipe_id:
            if rid not in recipe_pair_id:
                recipe_pair_id[rid] = list()
            recipe_pair_id[rid].append(macro)
        for name in macro.recipe_name:
            if name not in recipe_pair_name:
                recipe_pair_name[name] = list()
            recipe_pair_name[name].append(macro)
        _logger.debug(f"{macro.name} loaded")
    macros.sort(key=lambda x: x.time)
    for key in recipe_pair_id.keys(): recipe_pair_id[key].sort(key=lambda x: x.time)
    for key in recipe_pair_name.keys(): recipe_pair_name[key].sort(key=lambda x: x.time)


load()


def get_key(craft):
    return (
        craft.recipe.recipe_row.key,
        craft.player.lv,
        craft.player.craft,
        craft.player.control,
        craft.player.max_cp,
        craft.recipe.rlv,
        craft.recipe.max_difficulty,
        craft.recipe.max_quality - craft.current_quality,
        craft.recipe.max_durability,
    )


class MacroCraft(Solver):

    @staticmethod
    def suitable(craft):
        key = get_key(craft)
        if key not in macro_pairing:
            rid = craft.recipe.recipe_row.key
            if rid in recipe_pair_id:
                for macro in recipe_pair_id[rid]:
                    if macro.attr_pair(craft.player):
                        macro_pairing[key] = macro
                        return True
            rname = craft.recipe.name
            if rname in recipe_pair_name:
                for macro in recipe_pair_name[rname]:
                    if macro.attr_pair(craft.player):
                        macro_pairing[key] = macro
                        return True
            for macro in macros:
                ans = macro.pair(craft.clone())
                if ans is None:
                    _logger.debug(f"{macro.name} paired")
                    macro_pairing[key] = macro
                    return True
                else:
                    _logger.debug(f"{macro.name} is unpaired because: {ans}")
            macro_pairing[key] = None
        return macro_pairing[key] is not None

    def __init__(self, craft, logger):
        super().__init__(craft, logger)
        key = get_key(craft)
        _logger.debug("macro used:[%s]" % macro_pairing[key].name)
        self.runner = macro_pairing[key].macro.get_runner()
        self.param = get_params(craft, None)

    def process(self, craft, used_skill=None) -> str:
        if self.runner is None: return ''
        self.param = get_params(craft, None) | get_params(craft, used_skill)
        try:
            cmd, arg, wait = self.runner.next(self.param)
            while cmd != "ac":
                cmd, arg, wait = self.runner.next(self.param)
        except MacroFinish:
            self.runner = None
            return ''
        return arg.strip('"')
