from FFxivPythonTrigger import api

"""
114,贤者的叙事谣,30
116,军神的赞美歌,40
3559,放浪神的小步舞曲,52

3561,光阴神的礼赞凯歌,35
7408,大地神的抒情恋歌,66
7405,行吟,62

110,失血箭,12
117,死亡箭雨,45

101,猛者强击,4
107,纷乱箭,38
118,战斗之声,50

100,毒咬箭,6
113,风蚀箭,30
7406,烈毒咬箭,64
7407,狂风蚀箭,64
3560,伶牙俐齿,56

97,强力射击,1
98,直线射击,2
16495,爆发射击,76
7409,辉煌箭,70

106,连珠箭,18

3558,九天连箭,54
3562,侧风诱导箭,60
7404,完美音调,52
16494,影噬箭,72
16496,绝峰箭,80
"""
"""
122,直线射击预备
129,风蚀箭
1201,狂风蚀箭
124,毒咬箭
1200,烈毒咬箭

"""


def single(me):
    return 98 if 122 in me.effects.get_dict() else 97


def dot(me):
    lv = me.level
    target = api.XivMemory.targets.current
    if target is None: return 100
    poison, wind = (124, 129) if lv < 64 else (1200, 1201)
    t_effects = target.effects.get_dict()
    if poison not in t_effects or lv < 30: return 100
    if wind not in t_effects: return 113
    if lv > 56: return 3560
    return 100 if t_effects[poison].timer < t_effects[wind] else 113


combos = {
    98: single,  # 直线射击：自动直线
    3560: dot  # 伶牙俐齒：智能dot
}
