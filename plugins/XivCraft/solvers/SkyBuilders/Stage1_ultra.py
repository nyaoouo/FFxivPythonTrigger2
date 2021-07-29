from plugins.XivCraft.simulator import Manager
from FFxivPythonTrigger import api
from plugins.XivCraft.simulator.Craft import Craft
import math


def is_process_finished(craft: Craft) -> bool:
    """
    判断作业部分是否差一个制作完成
    :param craft:生产数据
    """
    temp = craft.clone()  # 创建数据副本
    temp.effects.clear()  # 清除状态
    temp.status = Manager.mStatus.DEFAULT_STATUS()  # 重设球色
    return temp.use_skill('制作').is_finished()  # 获取打一个制作后的数据是否满作业


def is_inner_quiet_finished(craft: Craft) -> bool:
    """
    获取內静是否已经达到要求（八层）
    :param craft: 生产数据
    """
    return craft.effects['内静'].param >= 8


def progess_skill(craft: Craft, skill: str) -> str:
    """
    对于作业类技能先模拟是否会搓爆，是的话打一个确认
    :param craft:  生产数据
    :param skill: 技能名
    :return: 决定使用的技能
    """
    temp = craft.clone().use_skill(skill)  # 创建数据副本并且使用技能
    if temp.is_finished():  # 判断是否满作业
        return '最终确认'
    else:
        return skill


class Stage1:
    def __init__(self):
        self.blueprint = sum([i.count for i in api.XivMemory.inventory.get_item_in_pages_by_key(28724, "backpack")])  # 获取背包图纸数量
        self.blueprint_used = 0  # 目前使用过的图纸数量
        self.count = 0  # 失败的高速次数
        self.count2 = 0  # 失败的专心次数
        self.process_calc_base = None  # 半个崇敬高速可以推多少作业（记分用）

    def score(self, craft: Craft) -> int:
        """
        对生产数据做出评估，给出分数
        :param craft: 生产数据
        :return: 评估分数
        """
        waste_not_score = 0 if "俭约" not in craft.effects else craft.effects["俭约"].param * 3  # 每一层俭约节省5点耐久，算60%利用率
        manipulation_score = 0 if '掌握' not in craft.effects else craft.effects['掌握'].param * 5  # 同上，不过不会浪费
        s = craft.current_durability * 2 + craft.current_cp  # 耐久转换cp算1:2
        s += waste_not_score + manipulation_score
        if not is_process_finished(craft):  # 算算大概差多少打满作业
            s -= math.ceil((craft.recipe.max_difficulty - craft.current_progress) / self.process_calc_base) * 10
        if craft.effects['内静'].param < 8:  # 算算大概差多少打满內静
            s -= (8 - craft.effects['内静'].param) * 10
        return s

    def is_finished(self, craft: Craft, prev_skill: str = None) -> bool:
        """
        接口，用于判断本stage是否负责下一步判断
        :param craft: 生产数据
        :param prev_skill: 上一个使用的技能名字
        """
        if self.process_calc_base is None:  # 算一下记分用的系数
            temp = Craft(craft.recipe, craft.player)
            temp.add_effect('崇敬', 9)
            temp.merge_effects()
            self.process_calc_base = temp.use_skill('高速制作').current_progress // 2
        return is_process_finished(craft) and is_inner_quiet_finished(craft)  # 需要推满作业+內静八层进下一个stage

    def deal(self, craft: Craft, prev_skill: str = None) -> str:
        """
        接口，用于获取下一步的解
        :param craft: 生产数据
        :param prev_skill: 上一个使用的技能名字
        :return: 下一步的建议技能
        """
        process_finish = is_process_finished(craft)

        #####
        # 一些计数的逻辑
        #####
        if prev_skill == '高速制作:fail':
            self.count += 1
        elif prev_skill == '专心加工:fail':
            self.count2 += 1
        elif prev_skill == '设计变动':
            self.blueprint_used += 1

        #####
        # 分数太低或者內静没了建议倒掉
        #####
        s = self.score(craft)
        if s < 400 or craft.effects['内静'].param < 2:
            return 'terminate'

        # if self.count > 4 or self.count2 > 2 or craft.current_cp < 300:
        #     return 'terminate'

        #####
        # 紫球处理
        #####
        if craft.status == "長持続":
            if not process_finish and '崇敬' not in craft.effects: return '崇敬'
            if craft.current_cp > 400:
                if '俭约' not in craft.effects: return '俭约'
                if '掌握' not in craft.effects: return '掌握'

        #####
        # 红球处理
        #####
        if craft.status == "高品质":
            if craft.current_durability > 10:
                if craft.effects['内静'].param < 9:
                    return '集中加工'
                else:
                    return progess_skill(craft, '集中制作')
            return '秘诀'

        empty_dur = craft.recipe.max_durability - craft.current_durability  # 消耗了多少耐久（用于判断精修一类）

        #####
        # 绿球处理
        #####
        if craft.status == "高效" and craft.current_cp >= 400:
            if '掌握' not in craft.effects: return '掌握'
            if empty_dur >= 30: return '精修'
            if '俭约' not in craft.effects: return '长期俭约'  # 这玩意我犹豫了很久加不加进去

        #####
        # 关于是否使用图纸的判断（仅仅在白球触发）
        # 计算“那些球色现在有用”，如果超过三个的话就刷球
        # 一般开场就消耗完三张了（笑
        #####
        if craft.status == "通常" and self.blueprint - self.blueprint_used and self.blueprint_used < 3:
            need_cnt = 0
            if not process_finish and '崇敬' in craft.effects and not is_process_finished(craft.clone().use_skill('高速制作')):
                need_cnt += 1
            if empty_dur >= 35 or ('掌握' not in craft.effects and empty_dur >= 5):
                need_cnt += 1
            if craft.effects['内静'].param < 9 and craft.current_durability > 10:
                need_cnt += 1
            if not process_finish and '崇敬' not in craft.effects:
                need_cnt += 1
            if need_cnt > 2:
                return '设计变动'

        #####
        # 耐久不足以使用下一个作业技能就打精修
        # 考虑过低于等于11就打，但是嘛（
        # ps. 应该考虑提高维修线防止下一个是黄球然后你莫得耐久了（放心，打出来专心一样炸）
        #####
        if craft.current_durability <= craft.get_skill_durability('制作'):
            return '精修'

        #####
        # 黄球处理
        #####
        if craft.status == "安定":
            if craft.effects['内静'].param < 7 and craft.current_durability > 10:
                return '专心加工'

        #####
        # 关于“其余”的处理
        # 如果深蓝球或者在崇敬就尝试推作业（会算一下不用高速的话就模范或者xxx）
        # 內静的话赌一下专心有助于提高分数！
        # 可以用俭约补最后几层的话还是俭约补吧，仓促太难了
        # 新增如果是黄球也进入（高速boom警告）
        #####
        if not process_finish and (craft.status == "高進捗" or '崇敬' in craft.effects or craft.status == "安定"):
            for s in '制作', '模范制作', '高速制作':
                if is_process_finished(craft.clone().use_skill(s)):
                    return progess_skill(craft, s)
            return progess_skill(craft, '高速制作')
        if craft.effects['内静'].param < 8:
            #####
            # 现在有伟大的黄球了，让我们把命运交给它吧（快进到黄球专心三连炸）
            #####
            # if craft.effects['内静'].param < 5:
            #     return '专心加工'
            return "仓促" if '俭约' in craft.effects or craft.status == "安定" else '俭约加工'
        else:
            return '崇敬'
