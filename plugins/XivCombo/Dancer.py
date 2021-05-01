from FFxivPythonTrigger import api

"""
15989：瀑泻（1）
15990：喷泉（2）
15991：逆瀑泻（20）
15992：坠喷泉（40）
15993：风车（15）
15994：落刃雨（25）
15995：升风车（35）
15996：落血雨（45）
16007：扇舞·序（30）
16008：扇舞·破（50）
16009：扇舞·急（66）
15997：标准舞步（15）
15998：技巧舞步（70）
16005：剑舞（76）
"""
"""
1814,逆瀑泻预备
1815,坠喷泉预备
1816,升风车预备
1817,落血雨预备
1818,标准舞步
1819,技巧舞步
1820,扇舞·急预备
1821,标准舞步结束
1822,技巧舞步结束
"""


def step_to_skill(step):
    return 15998 + step if step > 0 else 15999


def single(me):
    for eid, _ in me.effects.get_items():
        if eid == 1814:
            return 15991
        elif eid == 1815:
            return 15992
    if api.XivMemory.combat_data.combo_state.action_id == 15989 and me.level >= 2:
        return 15990
    return 15989


def multi(me):
    for eid, _ in me.effects.get_items():
        if eid == 1816:
            return 15995
        elif eid == 1817:
            return 15996
    if api.XivMemory.combat_data.combo_state.action_id == 15993 and me.level >= 25:
        return 15994
    return 15993


def standard(me):
    gauge = api.XivMemory.player_info.gauge
    if 1818 in me.effects.get_dict() and gauge.currentStep < 2:
        return step_to_skill(gauge.step[gauge.currentStep])
    return 15997


def skill(me):
    gauge = api.XivMemory.player_info.gauge
    if 1819 in me.effects.get_dict() and gauge.currentStep < 4:
        return step_to_skill(gauge.step[gauge.currentStep])
    return 15998


combos = {
    15994: multi,  # 落刃雨
    15990: single,  # 喷泉
    15997: standard,  # 标准舞步
    15998: skill,  # 技巧舞步
}
