from FFxivPythonTrigger import api

"""
7503,摇荡,2
7504,回刺,1
7505,赤闪雷,4
7506,短兵相接,6
7507,赤疾风,10
7509,散碎,15
7510,赤火炎,26
7511,赤飞石,30
7512,交击斩,35
7513,划圆斩,52
7514,赤治疗,54
7515,移转,40
7516,连攻,50
7517,飞刺,45
7518,促进,50
7519,六分反击,56
7520,鼓励,58
7521,倍增,60
7523,赤复活,64
7524,震荡,62
7525,赤核爆,68
7526,赤神圣,70
7527,魔回刺,1
7528,魔交击斩,35
7529,魔连攻,50
7530,魔划圆斩,52
7559,沉稳咏唱,44
7560,昏乱,8
7561,即刻咏唱,18
7562,醒梦,24
"""


def single(me):
    lv = me.level
    gauge = api.XivMemory.player_info.gauge
    white = gauge.white_mana <= gauge.black_mana
    effects = me.effects.get_dict()
    if 1249 in effects or 167 in effects:
        if white and lv >= 10: return 7507
        return 7505 if lv >= 4 else 7503
    else:
        if 1234 in effects and 1235 in effects:
            return 7511 if white else 7510
        if 1234 in effects:
            return 7510
        if 1235 in effects:
            return 7511
        return 7503


def multi(me):
    lv = me.level
    gauge = api.XivMemory.player_info.gauge
    white = gauge.white_mana <= gauge.black_mana
    effects = me.effects.get_dict()
    if 1249 in effects or 167 in effects:
        return 7509
    if white and lv >= 22:
        return 16525
    else:
        return 16524 if lv >= 18 else 7509


def sword(me):
    lv = me.level
    gauge = api.XivMemory.player_info.gauge
    white = gauge.white_mana <= gauge.black_mana
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 7504 and lv >= 35:
        return 7512
    elif combo_id == 7512 and lv >= 50:
        return 7516
    elif combo_id == 7529 and lv >= 68:
        if lv < 70: return 7525
        effects = me.effects.get_dict()
        if gauge.white_mana == gauge.black_mana:
            if 1234 in effects: return 7526
            if 1235 in effects: return 7525
        return 7526 if white and lv >= 70 else 7525
    elif (combo_id == 7525 or combo_id == 7526) and lv >= 80:
        return 16530
    else:
        return 7504


combos = {
    7510: single,  # 赤火炎
    7509: multi,  # 散碎
    7516: sword,  # 连攻
}
