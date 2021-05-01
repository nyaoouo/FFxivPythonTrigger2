from FFxivPythonTrigger import api

Unmend = 3624  # 伤残
HardSlash = 3617  # 重斩
SyphonStrike = 3623  # 吸收斩
Souleater = 3632  # 噬魂斩
Bloodspiller = 7392  # 血溅
Quietus = 7391  # 寂灭（64）
Delirium = 7390  # 血乱（68）

Unleash = 3621  # 释放
AbyssalDrain = 3641  # 吸血深渊
CarveAndSpit = 3643  # 精雕怒斩
StalwartSoul = 16468  # 刚魂
FloodOfDarkness = 16466  # 暗黑波动
EdgeOfDarkness = 16467  # 暗黑锋
BloodWeapon = 3625  # 嗜血

DeliriumStatus = 1972  # 血乱


def single_combo(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == HardSlash:
        return SyphonStrike if lv >= 2 else HardSlash
    elif combo_id == 3623:
        return Souleater if lv >= 26 else HardSlash
    else:
        return HardSlash


def multi_combo(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == Unleash and lv >= 72:
        return StalwartSoul
    return Unleash


combos = {
    Souleater: single_combo,
    StalwartSoul: multi_combo
}
