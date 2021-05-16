import time

from FFxivPythonTrigger.Logger import debug
from ...simulator.Craft import Craft, CheckUnpass
from ...simulator.Status import DEFAULT_STATUS

durReq = 21  # 留一个基础斩杀参考的耐久
cpReq = 131  # 留一个基础斩杀参考的cp
AllowBuffs = {'阔步', '改革', '俭约', }  # 需要考虑的buff # 在考虑是否塞长俭（隔壁已经塞了）
SpecialStatus = {"高品质", "结实", "高效", "長持続"}  # 一些”特殊球色“碰到的时候重新算一下


def allowSkills(craft):
    """
    获取某个数据下可以使用的技能

    *需要继续优化剪枝
    """
    remainCp = craft.current_cp - cpReq  # 算一下可以用的cp
    ans = list()  # 会把可选项塞里面

    if craft.status == "高品质":  # 红球的特殊照顾
        ans.append('秘诀')
        ans.append('集中加工')

    elif '观察' in craft.effects and craft.status.name not in SpecialStatus:
        return ['注视加工']  # 如果没啥特别球（可能是因为观测后特殊球需要重新算）观察后面就乖乖的接注视

    if remainCp < 0: return ans  # 如果没有剩余的cp，算个锤子

    if remainCp >= craft.get_skill_cost('精修') and craft.current_durability <= craft.recipe.max_durability - 30:
        ans.append('精修')  # 可以修就试着修

    if remainCp > 150 and '掌握' not in craft.effects and '改革' not in craft.effects and '阔步' not in craft.effects:
        ans.append('掌握')  # 掌握是一个好东西，可惜太吃cp

    for buff in AllowBuffs:  # 如果没有这些buff就把它们扔进去池子里面（象征性加个7来防止cp不够xjb按buff的煞笔支线）
        if buff not in craft.effects and remainCp >= craft.get_skill_cost(buff) + 7:
            ans.append(buff)

    if '改革' in craft.effects or remainCp < 50 or craft.status.name in SpecialStatus:
        to_add = list()  # 一个池子用来判定打算塞什么加工技能进去
        if '观察' in craft.effects:
            to_add.append('注视加工')  # 如果是因为特别球而进来的话，吧注视加工扔进去池子里面
        if '观察' not in craft.effects or craft.status.name in SpecialStatus:  # 当然，如果不是特殊球，就别把这些东西塞观察后面了
            to_add.append('坯料加工')
            if '俭约' not in craft.effects:
                to_add.append('俭约加工')
        for skill in to_add:  # 一个一个技能判断是不是一个”合法技能“
            if craft.current_durability > craft.get_skill_durability(skill) and remainCp >= craft.get_skill_cost(skill):
                ans.append(skill)

    # 如果改革或者阔步不是剩余一个回合就尝试观察打连击
    if not (('改革' in craft.effects and craft.effects['改革'].param == 1) or ('阔步' in craft.effects and craft.effects['阔步'].param == 1)):
        ans.append('观察')

    return ans  # 返回答案


def try_solve(craft: Craft, line_to_finish, timeLimit=None):
    # 一个传统的bfs
    best = (craft, [])  # 目前最佳项 第一个坑是数据，第二个是历史
    queue = [(craft, [])]  # 待办事项
    start = time.perf_counter()  # 开始的计时
    last_print = start  # 最后一次打印“临时方案”的时间
    while queue:  # 还有待办事项就继续
        if timeLimit is not None and time.perf_counter() - start > timeLimit:
            return best  # 超时了就直接返回
        if time.perf_counter() > last_print + 1:  # 打印一下临时方案证明不是程序炸了
            last_print = time.perf_counter()
            debug("solver bfs", "plan in {:.2f}s:{}({})".format(last_print - start, best[1], best[0].current_quality))
        t_craft, t_history = queue.pop(0)  # 获取一个待办事项
        for skill in allowSkills(t_craft):  # 获取可用的技能
            try:
                tt_craft = t_craft.clone()
                tt_craft.use_skill(skill, True)
            except CheckUnpass:
                continue
            if tt_craft.current_cp < cpReq:
                continue
            tt_craft.status = DEFAULT_STATUS()
            new_data = (tt_craft, t_history + [skill])  # 往上一坨都是模拟使用技能然后组成一个新的事项
            if tt_craft.current_durability >= durReq and tt_craft.current_quality > best[0].current_quality:
                if best[0].current_quality >= line_to_finish: return new_data  # 如果高于斩杀线就直接返回
                best = new_data  # 如果品质高点就存best
            queue.append(new_data)  # 把数据塞进去待办事项
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
    """
    一个弃用了的斩杀模块
    现在都接入astar了
    """

    def __init__(self):
        self.queue = ['阔步', '改革', '观察', '注视加工', '阔步', '比尔格的祝福', '制作'][:]

    def deal(self, craft, prev_skill=None):
        if len(self.queue) == 1 and craft.current_quality < 58000:
            return 'terminate'
        return self.queue.pop(0)

    def is_finished(self, craft, prev_skill=None):
        return not bool(self.queue)
