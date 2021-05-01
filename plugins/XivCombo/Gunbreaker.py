from FFxivPythonTrigger import api

"""
16143：闪雷弹（15）
16137：利刃斩（1）
16139：残暴弹（4）
16145：迅连斩（26）
16141：恶魔切（10）
16149：恶魔杀（40）
16162：爆发击（30）
16163：命运之环（72）
16153：音速破（54）
16146：烈牙（60）
16147：猛兽爪（60）
16150：凶禽爪（60）
16155：续剑（70）
16144：危险领域（18/80)
16159：弓形冲波(62)
16138：无情(2)
16164：血壤（76）
"""
status = [1842, 1843, 1844]


def single(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 16137 and lv >= 4:
        return 16139
    elif combo_id == 16139 and lv >= 26:
        return 16145
    else:
        return 16137


def multi(me):
    if api.XivMemory.combat_data.combo_state.action_id == 16141 and me.level >= 40:
        return 16149
    else:
        return 16141


def bullet(me):
    for eid, _ in me.effects.get_items():
        if eid in status:
            return 16155
    continuationState = api.XivMemory.player_info.gauge.continuationState
    if continuationState == 1:
        return 16147
    elif continuationState == 2:
        return 16150
    else:
        return 16146


combos = {
    16145: single,  # 迅连斩
    16149: multi,  # 恶魔杀
    16150: bullet,  # 凶禽爪
}
