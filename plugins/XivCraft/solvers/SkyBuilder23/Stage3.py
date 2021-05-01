import time

from FFxivPythonTrigger.Logger import debug
from plugins.XivCraft.simulator.Craft import Craft, CheckUnpass
from plugins.XivCraft.simulator.Status import DEFAULT_STATUS

durReq = 21
cpReq = 131
AllowBuffs = {'阔步', '改革', '俭约', }
SpecialStatus = {"高品质", "结实", "高效"}


def allowSkills(craft):
    remainCp = craft.current_cp - cpReq
    ans = list()

    if craft.status == "高品质":
        ans.append('秘诀')
        ans.append('集中加工')
    elif '观察' in craft.effects and craft.status.name not in SpecialStatus:
        return ['注视加工']
    if remainCp < 0: return ans
    if remainCp >= craft.get_skill_cost('精修') and craft.current_durability <= craft.recipe.max_durability - 30:
        ans.append('精修')
    if remainCp > 150 and '掌握' not in craft.effects and '改革' not in craft.effects and '阔步' not in craft.effects:
        ans.append('掌握')
    for buff in AllowBuffs:
        if buff not in craft.effects and remainCp >= craft.get_skill_cost(buff) + 7:
            ans.append(buff)
    if '改革' in craft.effects or remainCp < 50 or craft.status.name in SpecialStatus:
        to_add = list()
        if '观察' in craft.effects:
            to_add.append('注视加工')
        if '观察' not in craft.effects or craft.status.name in SpecialStatus:
            to_add.append('坯料加工')
            if '俭约' not in craft.effects:
                to_add.append('俭约加工')
        for skill in to_add:
            if craft.current_durability > craft.get_skill_durability(skill) and remainCp >= craft.get_skill_cost(skill):
                ans.append(skill)
    if not ('改革' in craft.effects and craft.effects['改革'].param == 1) and ('阔步' in craft.effects and craft.effects['阔步'].param == 1):
        ans.append('观察')
    return ans


def try_solve(craft: Craft, timeLimit=None):
    best = None
    queue = [(craft, [])]
    start = time.perf_counter()
    while queue:
        if timeLimit is not None and time.perf_counter() - start > timeLimit:
            return best
        t_craft, t_history = queue.pop(0)
        for skill in allowSkills(t_craft):
            try:
                tt_craft = t_craft.clone().use_skill(skill, True)
            except CheckUnpass:
                continue
            if tt_craft.current_cp < cpReq:
                continue
            tt_craft.status = DEFAULT_STATUS()
            new_data = (tt_craft, t_history + [skill])
            if tt_craft.current_durability >= durReq and (best is None or tt_craft.current_quality > best[0].current_quality):
                best = new_data
            queue.append(new_data)
    return best


class Stage3:
    def __init__(self):
        self.queue = []

    def is_finished(self, craft, prev_skill=None):
        if not bool(self.queue) or craft.status.name in SpecialStatus:
            start = time.perf_counter()
            ans = try_solve(craft, 8)
            if ans is not None:
                self.queue = ans[1]
                debug("solver dfs", "new plan in {:.2f}s:{}({})".format(time.perf_counter() - start, self.queue, ans[0].current_quality))
        return not bool(self.queue)

    def deal(self, craft, prev_skill=None):
        return self.queue.pop(0)
