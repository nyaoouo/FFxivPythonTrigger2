from FFxivPythonTrigger import api


def single(me):
    lv = me.level
    gauge = api.XivMemory.player_info.gauge
    white = gauge.white_mana <= gauge.black_mana
    effects = me.effects.get_dict()
    if 1249 in effects or 167 in effects:
        if white and lv >= 10: return 7507
        return 7505 if lv >= 4 else 7503
    else:
        if 1234 in effects: return 7510
        if 1235 in effects: return 7511
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
        return 7526 if white and lv >= 70 else 7525
    elif (combo_id == 7525 or combo_id == 7526) and lv >= 80:
        return 16530
    else:
        return 7504


combos = {
    7510:single,  # 赤火炎
    7509:multi,  # 散碎
    7516:sword,  # 连攻
}
