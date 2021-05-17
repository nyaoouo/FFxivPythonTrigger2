import time

from FFxivPythonTrigger.Logger import debug
from ...simulator.Craft import Craft, CheckUnpass
from ...simulator.Status import DEFAULT_STATUS

durReq = 21
cpReq = 131
AllowBuffs = {("阔步", "阔步"), ("改革", "改革"), ("俭约", "俭约")}
SpecialStatus = {"高品质", "结实", "高效", "長持続"}


def allowSkills(craft):
    remainCp = craft.current_cp - cpReq
    ans = list()

    if craft.status == "高品质":
        ans.append("秘诀")
        ans.append("集中加工")
    elif "观察" in craft.effects and craft.status.name not in SpecialStatus:
        return ["注视加工"]
    if remainCp < 0:
        return ans
    if (
        remainCp >= craft.get_skill_cost("精修")
        and craft.current_durability <= craft.recipe.max_durability - 30
    ):
        ans.append("精修")
    if (
        remainCp > 150
        and "掌握" not in craft.effects
        and "改革" not in craft.effects
        and "阔步" not in craft.effects
    ):
        ans.append("掌握")
    for buff, name in AllowBuffs:
        if (
            name not in craft.effects
            and craft.current_cp >= craft.get_skill_cost(buff) + 7
        ):
            ans.append(buff)
    if "改革" in craft.effects or remainCp < 50 or craft.status.name in SpecialStatus:
        to_add = list()
        if "观察" in craft.effects:
            to_add.append("注视加工")
        if "观察" not in craft.effects or craft.status.name in SpecialStatus:
            to_add.append("坯料加工")
            if "俭约" not in craft.effects:
                to_add.append("俭约加工")
        for skill in to_add:
            if craft.current_durability > craft.get_skill_durability(
                skill
            ) and remainCp >= craft.get_skill_cost(skill):
                ans.append(skill)
    if not (
        ("改革" in craft.effects and craft.effects["改革"].param == 1)
        or ("阔步" in craft.effects and craft.effects["阔步"].param == 1)
    ):
        ans.append("观察")
    return ans


def try_solve(craft: Craft, timeLimit=None):
    best = (craft, [])
    queue = [(craft, [])]
    start = time.perf_counter()
    last_print = start
    while queue:
        if timeLimit is not None and time.perf_counter() - start > timeLimit:
            return best
        if time.perf_counter() > last_print + 1:
            last_print = time.perf_counter()
            debug(
                "solver bfs",
                "plan in {:.2f}s:{}({})".format(
                    last_print - start, best[1], best[0].current_quality
                ),
            )
        t_craft, t_history = queue.pop(0)
        for skill in allowSkills(t_craft):
            try:
                tt_craft = t_craft.clone()
                tt_craft.use_skill(skill, True)
            except Exception:
                continue
            if tt_craft.current_cp < cpReq:
                continue
            tt_craft.status = DEFAULT_STATUS()
            new_data = (tt_craft, t_history + [skill])
            if (
                tt_craft.current_durability >= durReq
                and tt_craft.current_quality > best[0].current_quality
            ):
                best = new_data
            queue.append(new_data)
    return best


class Stage3:
    """
    stage模块，对接bfs搜索
    """

    def __init__(self):
        self.queue = []
        self.prev_skill = None
        self.line_to_finish = None

    def is_finished(self, craft, prev_skill=None):
        if self.line_to_finish is None:
            temp = Craft(craft.recipe, craft.player)
            temp.add_effect('内静', 11)
            temp.merge_effects()
            for s in ['阔步', '改革', '观察', '注视加工', '阔步', '比尔格的祝福', '制作']:
                temp.use_skill(s)
            self.line_to_finish = temp.recipe.max_quality - temp.current_quality
            debug("solver bfs", f"the line to finish is {self.line_to_finish}")
        if not bool(self.queue) or craft.status.name in SpecialStatus or prev_skill != self.prev_skill:
            start = time.perf_counter()
            ans = try_solve(craft, self.line_to_finish, 8)
            if ans[1]:
                self.queue = ans[1]
                debug("solver bfs", "new plan in {:.2f}s:{}({})".format(time.perf_counter() - start, self.queue, ans[0].current_quality))
        return len(self.queue) < 3 or craft.current_quality >= self.line_to_finish  # 这里是为了配合后续astar，让它有一点调整空间，同时如果高于斩杀线就直接下一步

    def deal(self, craft, prev_skill=None):
        self.prev_skill = self.queue.pop(0)
        return self.prev_skill


class StageEnd:
    def __init__(self):
        self.queue = ["阔步", "改革", "观察", "注视加工", "阔步", "比尔格的祝福", "制作"][:]

    def deal(self, craft, prev_skill=None):
        if len(self.queue) == 1 and craft.current_quality < 58000:
            return "terminate"
        return self.queue.pop(0)

    def is_finished(self, craft, prev_skill=None):
        return not bool(self.queue)
