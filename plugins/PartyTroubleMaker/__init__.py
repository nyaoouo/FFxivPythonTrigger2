from functools import cache, lru_cache

from FFxivPythonTrigger import *

from FFxivPythonTrigger.SaintCoinach import realm
from .Define import *

action_sheet = realm.game_data.get_sheet('Action')
job_sheet = realm.game_data.get_sheet('ClassJob')

last_damage_cache = dict()


def record_last_damage(actor_id: int, source_name: str, damage: int):
    last_damage_cache[actor_id] = (source_name, damage, api.XivMemory.actor_table.get_actor_by_id(actor_id).currentHP, time())


def get_last_damage(actor_id: int):
    if actor_id not in last_damage_cache: return None
    source_name, damage, current_hp, last_time = last_damage_cache[actor_id]
    if last_time < time() - 30: return None
    return f"{source_name}:{damage:,}/{current_hp:,}"


action_coll_down_cache = dict()


def member_use_action(actor_id: int, action_id: int):
    cd_gp, recast = action_cool_down_data(action_id)
    action_coll_down_cache[(actor_id, cd_gp)] = time() + recast


def get_member_action_cd(actor_id: int, action_id: int):
    cd_gp, recast = action_cool_down_data(action_id)
    key = (actor_id, cd_gp)
    if key not in action_coll_down_cache: return 0
    t = action_coll_down_cache[key] - time()
    if t > 0: return t
    del action_coll_down_cache[key]
    return 0


@cache
def action_name(action_id: int):
    return action_sheet[action_id]['Name']


@cache
def action_cool_down_data(action_id: int):
    row = action_sheet[action_id]
    return row['CooldownGroup'], row['Recast<100ms>'] / 10


@cache
def job_name(job_id: int):
    return job_sheet[job_id]['Name']


@lru_cache
def actor_name(actor_id):
    actor = api.XivMemory.actor_table.get_actor_by_id(actor_id)
    if actor is None: return f"unk_{actor_id}"
    # return f"{actor.Name}({actor_id:x})"
    return actor.Name


def is_in_party():
    return api.XivMemory.party.main_size > 1


def is_actor_in_party(actor_id: int):
    for actor in api.XivMemory.party.main_party():
        if actor.id == actor_id: return True
    return False


def action_display(action_id: int, source_id: int):
    return f"{action_name(action_id)}({actor_name(source_id)})"


DISABLE = 0
ECHO = 1
PARTY = 2

DEFAULT_MODE = ECHO


class PartyTroubleMaker(PluginBase):
    name = "PartyTroubleMaker"

    def __init__(self):
        super().__init__()
        self.storage.data.setdefault('config', dict())
        self.storage.save()
        self.register_event('network/action_effect', self.action_effect)
        self.register_event('network/actor_control/death', self.dead)
        self.register_event('network/actor_control/director_update/initial_commence', self.combat_reset)

    def _onunload(self):
        self.storage.save()

    def output(self, string, msg_key: str):
        mode = self.storage.data['config'].setdefault(msg_key, DEFAULT_MODE)
        if not mode: return
        cmd = '/p ' if mode == PARTY and is_in_party() else '/e '
        api.Magic.macro_command(cmd + string)

    def combat_reset(self,evt):
        action_coll_down_cache.clear()
        last_damage_cache.clear()

    def action_effect(self, event):
        if not is_in_party(): return
        if event.action_type == "action":
            source_name = action_display(event.action_id, event.source_id)
            if is_actor_in_party(event.source_id):
                member_use_action(event.source_id, event.action_id)
                naughty = list()
                if event.action_id in party_cover_skills:
                    for actor in api.XivMemory.party.main_party():
                        if actor.id not in event.targets and actor.currentHp:
                            naughty.append(actor_name(actor.id))
                elif event.action_id in party_cover_skills_except_source:
                    for actor in api.XivMemory.party.main_party():
                        if actor.id != event.source_id and actor.id not in event.targets and actor.currentHp:
                            naughty.append(actor_name(actor.id))
                if naughty:
                    self.output(f"{source_name} 未能覆盖：" + ', '.join(naughty), 'party_cover')
            is_danger = event.action_id in danger_skill
            for target_id, effects in event.targets.items():
                if not is_actor_in_party(target_id): continue
                if is_danger:
                    self.output(f"{actor_name(target_id)} 吃了好好吃的 {source_name}", 'danger_skill')
                for effect in effects:
                    if 'ability' in effect.tags:
                        record_last_damage(target_id, source_name, effect.param)
                    elif 'instant_death' in effect.tags:
                        record_last_damage(target_id, source_name, -1)

    def dead(self, event):
        if is_actor_in_party(event.target_id):

            msg = f"{actor_name(event.target_id)} 被 {actor_name(event.source_id)} 击杀：{get_last_damage(event.target_id) or '未知'}"
            self.output(msg, 'death_last_damage')

            member_have_swift = list()
            for actor in api.XivMemory.party.main_party():
                job = actor.job.raw_value
                if actor.currentHP and job in swift_res_jobs:
                    cd = get_member_action_cd(actor.id, 7561)
                    cd_msg = f"{cd:.1f}s" if cd else "ready"
                    member_have_swift.append((f"{job_name(job)}({actor.Name}):{cd_msg}", cd))
            if member_have_swift:
                member_have_swift.sort(key=lambda x: x[1])
                self.output("即刻咏唱冷却：" + (' / '.join([x[0] for x in member_have_swift])), 'death_count_swift')
            else:
                self.output("居然没有人可以复活，躺着吧你", 'death_count_swift')
