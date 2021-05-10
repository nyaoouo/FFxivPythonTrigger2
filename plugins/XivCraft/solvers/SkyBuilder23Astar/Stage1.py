from FFxivPythonTrigger.Logger import info
from plugins.XivCraft.simulator import Manager


class Stage1:
    def __init__(self):
        self.count = 0

    def is_finished(self, craft, prev_skill=None):
        temp = craft.clone()
        temp.effects.clear()
        temp.status = Manager.mStatus.DEFAULT_STATUS()
        return temp.use_skill('制作').is_finished()

    def deal(self, craft, prev_skill=None):
        if prev_skill == '高速制作:fail':
            self.count += 1
        if self.count > 4 or craft.effects['内静'].param < 2 or craft.craft_round >= 20 or craft.current_cp < 300:
            return 'terminate'
        if craft.status == "高效":
            if not '掌握' in craft.effects: return '掌握'
            if craft.current_durability < 20: return '精修'
        if craft.status == "高品质":
            if craft.effects['内静'].param < 10 and craft.current_durability > 10:
                return '集中加工'
            return '秘诀'
        if craft.status == "安定":
            if craft.effects['内静'].param < 6 and craft.current_durability > 10:
                return '专心加工'
        for s in '制作','模范制作','高速制作':
            temp=craft.clone().use_skill(s)
            if temp.current_durability <= 0:
                return '精修'
            if self.is_finished(temp):
                if temp.is_finished():
                    return '最终确认'
                else:
                    return s
        if '崇敬' in craft.effects:
            return '高速制作'
        else:
            return '崇敬'
