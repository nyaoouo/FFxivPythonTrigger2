from functools import cache, lru_cache

from FFxivPythonTrigger import *

from FFxivPythonTrigger.SaintCoinach import realm

action_sheet = realm.game_data.get_sheet('Action')

party_cover_skills = {
    133,  # 医济
    131,  # 愈疗
    124,  # 医治
    7433,  # 全大敕
    16534,  # 群花
    16536,  # 翅膀
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
    118,  # 战斗之声
    16004,  # 大舞
    16160,  # 光之心
    7388,  # 摆脱
    16471,  # 布道
}

last_damage_cache = dict()


def record_last_damage(actor_id: int, source_name: str, damage: int):
    last_damage_cache[actor_id] = (source_name, damage,api.XivMemory.actor_table.get_actor_by_id(actor_id).currentHP, time())


def get_last_damage(actor_id: int):
    if actor_id not in last_damage_cache: return None
    source_name, damage,current_hp, last_time = last_damage_cache[actor_id]
    if last_time < time() - 30: return None
    return f"{source_name}:{damage}/{current_hp}"


@cache
def action_name(action_id):
    return action_sheet[action_id]['Name']


@lru_cache
def actor_name(actor_id):
    return api.XivMemory.actor_table.get_actor_by_id(actor_id).Name


def is_in_party():
    return api.XivMemory.party.main_size > 1


def is_actor_in_party(actor_id: int):
    for actor in api.XivMemory.party.main_party():
        if actor.id == actor_id: return True
    return False


def action_display(action_id: int, source_id: int):
    return f"{action_name(action_id)}({actor_name(source_id)})"


class PartyTroubleMaker(PluginBase):
    name = "PartyTroubleMaker"

    def __init__(self):
        super().__init__()
        self.register_event('network/action_effect', self.action_effect)
        self.register_event('network/actor_control/death', self.dead)

    def output(self, string):
        api.Magic.macro_command("/e " + string)

    def action_effect(self, event):
        if not is_in_party(): return
        if event.action_type == "action":
            source_name = action_display(event.action_id, event.source_id)
            if event.action_id in party_cover_skills and is_actor_in_party(event.source_id):
                naughty = list()
                for actor in api.XivMemory.party.main_party():
                    if actor.id not in event.targets:
                        naughty.append(actor_name(actor.id))
                if naughty:
                    self.output(f"{source_name} 未能覆盖：" + ', '.join(naughty))
            for target_id, effects in event.targets.items():
                if not is_actor_in_party(target_id): continue
                for effect in effects:
                    if 'ability' in effect.tags:
                        record_last_damage(target_id, source_name, effect.param)
                    elif 'instant_death' in effect.tags:
                        record_last_damage(target_id, source_name, -1)

    def dead(self, event):
        if is_actor_in_party(event.target_id):
            self.output(f"{actor_name(event.target_id)} 被 {actor_name(event.source_id)} 击杀：{get_last_damage(event.target_id) or '未知'}")
