class Stage2:
    def __init__(self):
        self.count = 0

    def is_finished(self, craft, prev_skill=None):
        return not craft.effects['内静'].param < 8

    def deal(self, craft, prev_skill=None):
        if prev_skill == '专心加工:fail':
            self.count += 1
        if craft.craft_round >= 25 or craft.current_cp < 300 or self.count >= 2:
            return 'terminate'
        if craft.status == "高效":
            if not '掌握' in craft.effects: return '掌握'
            if craft.current_durability < 20: return "精修"
        if craft.current_durability <= 10:
            return "精修"
        if craft.status == "長持続":
            if not '掌握' in craft.effects: return '掌握'
            if not '俭约' in craft.effects: return '俭约'
        if craft.status == "高品质":
            if craft.effects['内静'].param < 10:
                return "集中加工"
            return "秘诀"
        if craft.clone().use_skill('专心加工').current_durability <= 0:
            return "精修"
        if 1 < craft.effects['内静'].param < 6:
            return '专心加工'
        if not '俭约' not in craft.effects:
            return "俭约加工"
        return "仓促"
