import time
from traceback import format_exc

from FFxivPythonTrigger.Logger import debug
from ...simulator.Craft import Craft, CheckUnpass
from ...simulator.Status import DEFAULT_STATUS

AllowBuffs = {
    ('阔步', '阔步'),
    ('改革', '改革'),
    ('俭约', '俭约'),
    # ('长期俭约', '俭约')
}
SpecialStatus = {"高品质", "结实", "高效"}


def allowSkills(craft):
    ans = list()

    if craft.status == "高品质":
        ans.append('秘诀')
        if craft.current_durability > craft.get_skill_durability('集中加工'):
            ans.append('集中加工')
    elif '观察' in craft.effects and craft.status.name not in SpecialStatus:
        return ['注视加工']
    if craft.current_cp < 0: return ans
    if '阔步' not in craft.effects or craft.effects['阔步'].param != 1:
        if craft.current_cp >= craft.get_skill_cost('精修') and craft.current_durability <= craft.recipe.max_durability - 30:
            ans.append('精修')
        if craft.current_cp > 150 and '掌握' not in craft.effects and '改革' not in craft.effects and '阔步' not in craft.effects:
            ans.append('掌握')
        for buff, name in AllowBuffs:
            if name not in craft.effects and craft.current_cp >= craft.get_skill_cost(buff) + 7:
                ans.append(buff)
    if '改革' in craft.effects or craft.current_cp < 60 or craft.status.name in SpecialStatus:
        to_add = list()
        if '观察' in craft.effects:
            to_add.append('注视加工')
        if '观察' not in craft.effects or craft.status.name in SpecialStatus:
            to_add.append('坯料加工')
            if '俭约' not in craft.effects:
                to_add.append('俭约加工')
        if craft.current_cp < 80:
            to_add.append('比尔格的祝福')
        for skill in to_add:
            if craft.current_durability > craft.get_skill_durability(skill) and craft.current_cp >= craft.get_skill_cost(skill):
                ans.append(skill)
    if not (('改革' in craft.effects and craft.effects['改革'].param == 1) or ('阔步' in craft.effects and craft.effects['阔步'].param == 1)):
        ans.append('观察')
    return ans


def try_solve(craft: Craft, timeLimit=None):
    best = (craft, [])
    best_un_finish = None
    best_start_with = None
    best_start_with_l = 0
    queue = [(craft, [])]
    start = time.perf_counter()
    last_print = start
    while queue:
        if timeLimit is not None and time.perf_counter() - start > timeLimit:
            return best
        if time.perf_counter() > last_print + 1:
            last_print = time.perf_counter()
            debug("solver astar", "plan in {:.2f}s:{}({})".format(last_print - start, best[1], best[0].current_quality))
        t_craft, t_history = queue.pop(0)
        if best_start_with is not None and len(t_history) > 8 and t_history[:best_start_with_l] != best_start_with:
            continue
        skills = allowSkills(t_craft)
        for skill in skills:
            try:
                try:
                    tt_craft = t_craft.clone()
                    tt_craft.use_skill(skill, True)
                except CheckUnpass:
                    continue
            except Exception:
                debug("solver astar", 'error at testing skill %s:\n%s' % (skill, t_craft))
                debug("solver astar", format_exc())
                continue
            tt_craft.status = DEFAULT_STATUS()
            new_data = (tt_craft, t_history + [skill])
            if tt_craft.current_durability >= 1 and tt_craft.current_quality > best[0].current_quality:
                if tt_craft.current_quality >= tt_craft.recipe.max_quality: return new_data
                best = new_data
            if skill != "比尔格的祝福":
                if tt_craft.current_durability >= 1 and (best_un_finish is None or tt_craft.current_quality > best_un_finish[0].current_quality):
                    best_un_finish = new_data
                    l = len(new_data[1])
                    c = (l // 4) + 1
                    if l >= 8:
                        best_start_with = new_data[1][:c]
                        best_start_with_l = c
                queue.append(new_data)
    return best


TIME_LIMIT = 8


class Stage3:
    def __init__(self):
        self.queue = []
        self.is_first = True

    def is_finished(self, craft, prev_skill=None):
        if self.is_first:
            debug("solver astar", "try to solve:\n%s" % craft.simple_str())
            self.is_first = False
        if not bool(self.queue) or craft.status.name in SpecialStatus:
            start = time.perf_counter()
            ans = try_solve(craft, TIME_LIMIT)
            if ans[1]:
                debug("solver astar", "new plan in {:.2f}s:{}({})".format(time.perf_counter() - start, ans[1], ans[0].current_quality))
                self.queue = ans[1] # if time.perf_counter() - start < TIME_LIMIT else ans[1][:4]
        return not bool(self.queue)

    def deal(self, craft, prev_skill=None):
        return self.queue.pop(0)


class StageEnd:
    def __init__(self):
        self.queue = ['制作']

    def deal(self, craft, prev_skill=None):
        if len(self.queue)==1 and craft.current_quality<58000:
            return 'terminate'
        return self.queue.pop(0)

    def is_finished(self, craft, prev_skill=None):
        return not bool(self.queue)
