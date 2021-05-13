from plugins.XivCraft.simulator import Manager
from FFxivPythonTrigger import api


def is_process_finished(craft):
    temp = craft.clone()
    temp.effects.clear()
    temp.status = Manager.mStatus.DEFAULT_STATUS()
    return temp.use_skill('制作').is_finished()


def is_inner_quiet_finished(craft):
    return craft.effects['内静'].param >= 8


def progess_skill(craft, skill):
    temp = craft.clone().use_skill(skill)
    if temp.is_finished():
        return '最终确认'
    else:
        return skill


class Stage1:
    def __init__(self):
        self.blueprint = sum([i.count for i in api.XivMemory.inventory.get_item_in_pages_by_key(28724, "backpack")])
        self.blueprint_used = 0
        self.count = 0
        self.count2 = 0

    def is_finished(self, craft, prev_skill=None):
        return is_process_finished(craft) and is_inner_quiet_finished(craft)

    def deal(self, craft, prev_skill=None):
        process_finish = is_process_finished(craft)
        if prev_skill == '高速制作:fail':
            self.count += 1
        elif prev_skill == '专心加工:fail':
            self.count2 += 1
        elif prev_skill == '设计变动':
            self.blueprint_used += 1

        if self.count > 4 or self.count2 > 2 or craft.current_cp < 300:
            return 'terminate'

        if craft.status == "長持続":
            if not process_finish and '崇敬' not in craft.effects: return '崇敬'
            if craft.current_cp > 400:
                if '俭约' not in craft.effects: return '俭约'
                if '掌握' not in craft.effects: return '掌握'

        if craft.status == "高品质":
            if craft.current_durability > 10:
                if craft.effects['内静'].param < 9:
                    return '集中加工'
                else:
                    return progess_skill(craft, '集中制作')
            return '秘诀'
        empty_dur = craft.recipe.max_durability - craft.current_durability
        if craft.status == "高效" and craft.current_cp >= 400:
            if '掌握' not in craft.effects: return '掌握'
            if empty_dur >= 30: return '精修'
            if '俭约' not in craft.effects: return '长期俭约'

        if craft.status == "通常" and self.blueprint - self.blueprint_used and self.blueprint_used < 3:
            need_cnt = 0
            if not process_finish and craft.status != "高進捗" and '崇敬' in craft.effects and not is_process_finished(craft.clone().use_skill('高速制作')):
                need_cnt += 1
            if empty_dur >= 35 or ('掌握' not in craft.effects and empty_dur >= 5):
                need_cnt += 1
            if craft.effects['内静'].param < 9 and craft.current_durability > 10:
                need_cnt += 1
            if not process_finish and '崇敬' not in craft.effects:
                need_cnt += 1
            if need_cnt > 2:
                return '设计变动'

        if craft.current_durability <= craft.get_skill_durability('制作'):
            return '精修'
        if not process_finish and (craft.status == "高進捗" or '崇敬' in craft.effects):
            for s in '制作', '模范制作', '高速制作':
                if is_process_finished(craft.clone().use_skill(s)):
                    return progess_skill(craft, s)
            return progess_skill(craft, '高速制作')
        if craft.effects['内静'].param < 8:
            if craft.effects['内静'].param < 5:
                return '专心加工'
            return "仓促" if '俭约' in craft.effects else '俭约加工'
        else:
            return '崇敬'
