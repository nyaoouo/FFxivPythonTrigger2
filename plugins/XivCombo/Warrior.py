from FFxivPythonTrigger import api


def single(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    red = None
    for eid, effect in me.effects.get_items():
        if eid == 90:
            red = effect
            break
    if combo_id == 31 and lv >= 4:
        return 37
    elif combo_id == 37 and lv >= 26:
        if red is not None and red.timer > 5 or lv < 50:
            return 42
        return 45
    return 31


def multi(me):
    if api.XivMemory.combat_data.combo_state.action_id == 41 and me.level >= 40:
        return 16462
    return 41


combos = {
    42: single,  # 暴风斩
    16462: multi,  # 秘银暴风
}
