from FFxivPythonTrigger import api

"""
2866：分裂弹
2868：独头弹
2872：热弹
2876：整备
2874：虹吸弹
2870：散射
2873：狙击弹
17209：超荷
7410：热冲击
2864：炮塔
2878：野火
2890：弹射
16497：自动弩
16498：钻头
7414：枪管加热
16499：毒菌
"""


def single(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    overheat = api.XivMemory.player_info.gauge.overheatMilliseconds
    if overheat and lv >= 35: return 7410
    if combo_id == 2866:
        return 2868 if lv >= 2 else 2866
    if combo_id == 2868:
        return 2873 if lv >= 26 else 2866
    return 2866


def multi(me):
    lv = me.level
    overheat = api.XivMemory.player_info.gauge.overheatMilliseconds
    return 16497 if overheat and lv >= 52 else 2870

combos = {
    2873: single,
    2870: multi
}
