from importlib import import_module
from pathlib import Path

from FFxivPythonTrigger.Logger import info

party_cover_skills = {
    133,  # 医济
    131,  # 愈疗
    124,  # 医治
    7433,  # 全大敕
    16534,  # 群花
    803,  # 低语
    16550,  # 大低语
    16551,  # 大幻光
    16547,  # 慰藉
    805,  # 幻光
    16544,  # 祥光
    186,  # 士气高扬
    3600,  # 阳星
    3601,  # 阳星相位
    16552,  # 占卜
    16553,  # 天星冲日
    16557,  # 天宫图
    16012,  # 桑巴
    16889,  # 策动
    7405,  # 行吟
    16004,  # 大舞
    16160,  # 光之心
    7388,  # 摆脱
    16471,  # 布道
    7459,  # 灵护
}

party_cover_skills_except_source = {
    # 118,  # 战斗之声
    # 3559,  # 放浪神
    # 114,  # 贤者
    # 116,  # 军神
}

danger_skill = set()
skill_alone = set()
skill_together = dict()

swift_res_jobs = {
    24,  # whm
    27,  # smn
    28,  # sch
    33,  # ast
    35,  # rdm
}
healer = {
    24,  # whm
    28,  # sch
    33,  # ast
}
damage_reduce = {
    1206, 849,  # 命运之轮
    1176,  # 武装
    1873,  # 节制
    299,  # 野战治疗阵
    1951,  # 策动
    1934,  # 行吟
    1826,  # 防守之桑巴
    1840,  # 石之心
    1832,  # 伪装
    1191,  # 铁壁
    1834,  # 星云
    1858,  # 原初的武猛
    735,  # 原初的直觉
    912,  # 受伤减轻（复仇）
    747,  # 暗影墙
    194,  # 铜墙铁盾
    195,  # 坚守要塞
    864,  # 暗黑之力
    863,  # 原初大地
    1931,  # 灵魂之青
    196,  # 终极堡垒
}
magic_damage_reduce = {
    317,  # 异想的幻光
    1875,  # 炽天的幻光
    1839,  # 光之心
    1894,  # 暗黑布道
    746,  # 弃明投暗
}
shield = {
    727,  # 圣光幕帘
    837,  # 黑夜领域
    1880,  # 天星冲日（夜）
    1898,  # 残暴弹
    1170,  # 至黑之夜
    297,  # 鼓舞
    1918,  # 激励
    1457,  # 摆脱
    1917,  # 炽天的幕帘
    1404,  # 神祝祷
    168,  # 魔罩
}
enemy_damage_reduce = {
    1193,  # 雪仇
}
enemy_physic_damage_reduce = {
    1195,  # 牵制
}
enemy_magic_damage_reduce = {
    1203,  # 昏乱
}

common_attack_name = {
    '攻击', ''
}

ability_type = {
    'fire': "火属",
    'ice': "冰属",
    'wind': "风属",
    'ground': "土属",
    'thunder': "雷属",
    'water': "水属",
    'unaspected': "无属",
    'physics': "物理",
    'magic': "魔法",
    'blow': "斩击",
    'slash': "突刺",
    'spur': "打击",
    'shoot': "射击",
    'diablo': "暗黑",
    'limit_break': "LB",
}

for f in (Path(__file__).parent / 'datas').glob('*.py'):
    if f.stem == '__init__': continue
    module = import_module(f'..datas.{f.stem}', __name__)
    if hasattr(module, 'danger_skill') and isinstance(module.danger_skill, set):
        danger_skill |= module.danger_skill
    if hasattr(module, 'skill_alone') and isinstance(module.skill_alone, set):
        skill_alone |= module.skill_alone
    if hasattr(module, 'skill_together') and isinstance(module.skill_together, dict):
        skill_together |= module.skill_together
damage_reduce |= magic_damage_reduce
enemy_damage_reduce |= enemy_physic_damage_reduce | enemy_magic_damage_reduce
