import re

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.MacroParser import Macro, MacroFinish
from pathlib import Path

from ...simulator.Status import DEFAULT_STATUS
from .. import Solver
from ...simulator.Craft import Craft, CheckUnpass

_logger = Logger("CraftMacroSolver")

default_params = {'status': DEFAULT_STATUS()}
macro_dir = Path(__file__).parent / 'macros'
macros = list()
macro_craft_tag_regex = re.compile(r"#CraftMacro:\[(?P<key>[^]]+)]:(?P<arg>[^\n]+)\n")
macro_max_size = 100
macro_pairing = dict()


class MacroOversize(Exception):
    pass


def load():
    macros.clear()
    macro_pairing.clear()
    for file in macro_dir.glob("*.macro"):
        with open(file, encoding='utf-8') as f:
            macro_str = f.read()
        tags = {gp[0]: gp[1] for gp in macro_craft_tag_regex.findall(macro_str)}
        tags['_file'] = file.stem
        macro = Macro(macro_str)
        runner = macro.get_runner()
        count = 0
        size = 0
        try:
            while True:
                try:
                    cmd, arg, wait_time = runner.next(default_params)
                    count += wait_time
                    size += 1
                    if size >= macro_max_size:
                        _logger.warning('a macro with size overload at file "%s" (max size:%s)' % (file, macro_max_size))
                        raise MacroOversize()
                except MacroFinish:
                    break
            _logger.debug('load macro [%s]' % (tags['Name'] if 'Name' in tags else tags['_file']))
            macros.append((count, macro, tags))
        except MacroOversize:
            continue

    macros.sort(key=lambda x: x[0])


class MacroCraft(Solver):
    @staticmethod
    def suitable(craft):
        key = (
            craft.player.lv,
            craft.player.craft,
            craft.player.control,
            craft.player.max_cp,
            craft.recipe.rlv,
            craft.recipe.max_difficulty,
            craft.recipe.max_quality - craft.current_quality,
            craft.recipe.max_durability,
        )
        if key not in macro_pairing:
            for time, macro, tags in macros:
                t_craft = craft.clone()
                runner = macro.get_runner()
                size = 0
                while True:
                    try:
                        size += 1
                        if size >= macro_max_size:
                            raise MacroOversize()
                        cmd, arg, wait = runner.next(default_params)
                        while cmd != "ac":
                            cmd, arg, wait = runner.next(default_params)
                        t_craft.use_skill(arg.strip('"'), check_mode=True)
                        if t_craft.is_finished():
                            if t_craft.current_quality >= t_craft.recipe.max_quality:
                                macro_pairing[key] = macro
                                break
                            else:
                                break
                    except MacroFinish:
                        break
                    except MacroOversize:
                        break
                    except CheckUnpass:
                        break
                # _logger.debug(tags["Name"],t_craft)
                if key in macro_pairing:
                    break
            if key not in macro_pairing:
                macro_pairing[key] = None
        return macro_pairing[key] is not None

    def __init__(self, craft, logger):
        super().__init__(craft, logger)
        key = (
            craft.player.lv,
            craft.player.craft,
            craft.player.control,
            craft.player.max_cp,
            craft.recipe.rlv,
            craft.recipe.max_difficulty,
            craft.recipe.max_quality - craft.current_quality,
            craft.recipe.max_durability,
        )
        self.runner = macro_pairing[key].get_runner()

    def process(self, craft, used_skill=None) -> str:
        if self.runner is None: return ''
        params = {'status': craft.status, 'prev': used_skill}
        try:
            cmd, arg, wait = self.runner.next(params)
            while cmd != "ac":
                cmd, arg, wait = self.runner.next(params)
        except MacroFinish:
            self.runner = None
            return ''
        return arg.strip('"')


load()
