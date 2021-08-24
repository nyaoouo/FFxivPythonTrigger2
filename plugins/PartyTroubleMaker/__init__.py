from functools import cache, lru_cache
from datetime import datetime
# from PyQt5.QtGui import QFont
# from PyQt5.QtWidgets import QGridLayout, QListWidget

from FFxivPythonTrigger import *
# from FFxivPythonTrigger.QT import FloatWidget, ui_loop_exec

from FFxivPythonTrigger.SaintCoinach import realm
from .Define import *

command = "@ptm"

action_sheet = realm.game_data.get_sheet('Action')
status_sheet = realm.game_data.get_sheet('Status')
job_sheet = realm.game_data.get_sheet('ClassJob')

last_damage_cache = dict()


def record_last_damage(actor_id: int, source_name: str, damage: int, reduced_damage=''):
    damage = f"{damage:,}"
    current = time()
    actor = api.XivMemory.actor_table.get_actor_by_id(actor_id)
    # if actor.shield_percent:
    #     shield = int(actor.maxHP * actor.shield_percent / 100)
    #     current_hp = f"{actor.currentHP + shield:,}({actor.currentHP}+{shield})"
    # else:
    #     current_hp = f"{actor.currentHP:,}"
    current_hp = f"{actor.currentHP:,}"
    if actor_id in last_damage_cache:
        source_name_old, damage_old, old_hp, reduced_damage_old, last_time = last_damage_cache[actor_id]
        if current - last_time < 0.1 and old_hp == current_hp:
            source_name += '+' + source_name_old
            damage += '+' + damage_old
            if reduced_damage_old != reduced_damage:
                reduced_damage += ' & ' + reduced_damage_old
    last_damage_cache[actor_id] = (source_name, damage, current_hp, reduced_damage, current)


def get_last_damage(actor_id: int):
    if actor_id not in last_damage_cache: return None
    source_name, damage, current_hp, reduced_damage, last_time = last_damage_cache[actor_id]
    if last_time < time() - 30: return None
    msg = f"{source_name}:{damage}/{current_hp}"
    if reduced_damage: msg += " - " + reduced_damage
    return msg


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
    if actor_id == 0xe0000000: return '-'
    actor = api.XivMemory.actor_table.get_actor_by_id(actor_id)
    if actor is None: return f"unk_{actor_id:x}"
    # return f"{actor.Name}({actor_id:x})"
    return actor.Name


@cache
def status_name(status_id: int):
    return status_sheet[status_id]['Name']


def is_in_party():
    return api.XivMemory.party.main_size > 1


def is_actor_in_party(actor_id: int):
    for actor in api.XivMemory.party.main_party():
        if actor.id == actor_id: return True
    return False


def action_display(action_id: int, source_id: int):
    return f"{action_name(action_id)}({actor_name(source_id)})"


death_count = dict()

DISABLE = 0
ECHO = 1
PARTY = 2

DEFAULT_MODE = ECHO


class PartyTroubleMaker(PluginBase):
    name = "PartyTroubleMaker"

    def __init__(self):
        super().__init__()
        # from pandas.io.clipboard import copy

        # class ListWindow(FloatWidget):
        #     allow_frameless = True
        #
        #     def __init__(self):
        #         super().__init__()
        #         self.setWindowTitle("PartyTroubleMaker")
        #         self.listWidget = QListWidget()
        #         #self.listWidget.itemSelectionChanged.connect(self.selectionChanged)
        #         self.setFont(QFont('Times', 16))
        #         self.layout = QGridLayout()
        #         self.layout.addWidget(self.listWidget)
        #         self.setLayout(self.layout)

        # def selectionChanged(self):
        #     copy('\n'.join([item.text() for item in self.listWidget.selectedItems()]))

        self.lock = Lock()
        self.storage.data.setdefault('config', dict())
        self.storage.save()
        self.last_death_count = 0
        self.register_event('network/action_effect', self.action_effect)
        self.register_event('network/actor_control/death', self.dead)
        self.register_event('network/combat_reset', self.combat_reset)
        # self.window: ListWindow = ui_loop_exec(ListWindow)
        api.command.register(command, self.process_command)

    def _start(self):
        # ui_loop_exec(self.window.show)
        pass

    def _onunload(self):
        # ui_loop_exec(self.window.full_close)
        api.command.unregister(command)

    def get_mode(self, key: str):
        return self.storage.data['config'].setdefault(key, DEFAULT_MODE)

    def output(self, string, msg_key: str):
        mode = self.get_mode(msg_key)
        if not mode: return
        if mode > DISABLE:
            self.logger.info(string)
            # ui_loop_exec(self.window.listWidget.addItem, f"[{datetime.now().strftime('%H:%M:%S')}] {string}")
            # ui_loop_exec(self.window.listWidget.scrollToBottom)
        if mode == PARTY: api.Magic.macro_command("/p " + string)

    def combat_reset(self, evt):
        action_coll_down_cache.clear()
        last_damage_cache.clear()
        death_count.clear()

    def action_effect(self, event):
        with self.lock:
            if not is_in_party(): return
            if event.action_type == "action":
                source_name = action_display(event.action_id, event.source_id)
                if is_actor_in_party(event.source_id):
                    # 记录cd
                    member_use_action(event.source_id, event.action_id)

                    # 发送不吃团辅的坏蛋
                    naughty = list()
                    if event.action_id in party_cover_skills:
                        for actor in api.XivMemory.party.main_party():
                            if actor.id not in event.targets and actor.currentHP:
                                naughty.append(actor_name(actor.id))
                    elif event.action_id in party_cover_skills_except_source:
                        for actor in api.XivMemory.party.main_party():
                            if actor.id != event.source_id and actor.id not in event.targets and actor.currentHP:
                                naughty.append(actor_name(actor.id))
                    if naughty:
                        self.output(f"{source_name} 未能覆盖：" + ', '.join(naughty), 'party_cover')

                is_danger = event.action_id in danger_skill
                take_member = []
                for target_id, effects in event.targets.items():
                    if not is_actor_in_party(target_id): continue
                    take_member.append(target_id)

                    # 发送吃shit队友
                    if is_danger: self.output(f"{actor_name(target_id)} 吃了好好吃的 {source_name}", 'danger_skill')

                    # 记录最后伤害
                    for effect in effects:
                        if 'ability' in effect.tags:
                            r = set()
                            sh = set()
                            t = api.XivMemory.actor_table.get_actor_by_id(target_id)
                            if t is not None:
                                t_e = {eid for eid, _ in t.effects.get_items()}
                                r = t_e.intersection(damage_reduce)
                                sh = t_e.intersection(shield)
                                s = api.XivMemory.actor_table.get_actor_by_id(event.source_id)
                                if s is not None: r |= {eid for eid, _ in s.effects.get_items()}.intersection(enemy_damage_reduce)
                            rs = ""
                            if r: rs = "减伤：" + "/".join([status_name(eid) for eid in r])
                            if sh: rs += f"+{t.shield_percent}%盾(≈{t.maxHP * t.shield_percent / 100:,.0f})：" + "/".join(
                                [status_name(eid) for eid in sh])
                            record_last_damage(target_id, source_name, effect.param, rs)
                            me = api.XivMemory.actor_table.get_me()
                            if me is not None and target_id == me.id and action_name(event.action_id) not in common_attack_name:
                                tag = ','.join([ability_type[tag] for tag in effect.tags if tag in ability_type])
                                self.output(f"{source_name} {effect.param}({tag}) {rs}", 'damage_reduce')
                        elif 'instant_death' in effect.tags:
                            record_last_damage(target_id, source_name, -1)

                if len(take_member) > 1 and event.action_id in skill_alone:
                    names = '，'.join([actor_name(mid) for mid in take_member])
                    self.output(f"{names} 暖心地分享了 {source_name}", 'danger_skill')
                elif event.action_id in skill_together and 0 < len(take_member) < skill_together[event.action_id]:
                    names = '，'.join([actor_name(mid) for mid in take_member])
                    self.output(f"{names} 自私地{'独吞' if len(take_member) == 1 else '瓜分'}了 {source_name}", 'danger_skill')

    def dead(self, event):
        with self.lock:
            if is_actor_in_party(event.target_id):
                if event.target_id not in death_count:
                    death_count[event.target_id] = 1
                else:
                    death_count[event.target_id] += 1

                # 发送死因
                msg = f"{actor_name(event.target_id)} 被 {actor_name(event.source_id)} 击杀：{get_last_damage(event.target_id) or '未知'}"
                self.output(msg, 'death_last_damage')

                if self.last_death_count < time():
                    # 发送即刻复活情况
                    member_have_swift = list()
                    has_healer = False
                    has_other = False
                    for actor in api.XivMemory.party.main_party():
                        job = actor.job.raw_value
                        if actor.currentHP and job in swift_res_jobs:
                            cd = get_member_action_cd(actor.id, 7561)
                            cd_msg = f"{cd:.1f}s" if cd else "就绪"
                            if actor.currentMP >= 2400 and (not cd or job == 35):
                                if job in healer:
                                    has_healer = True
                                else:
                                    has_other = True
                            member_have_swift.append((f"{job_name(job)}({actor.Name}):即刻{cd_msg}，蓝量{actor.currentMP}", cd))
                    member_have_swift.sort(key=lambda x: x[1])
                    if not member_have_swift:
                        msg = f"没有人可以给 {actor_name(event.target_id)} 复活了，安息吧"
                    else:
                        msg = f"复活工具人{len(member_have_swift)}个：\n"
                        msg += ' \n '.join([x[0] for x in member_have_swift])
                        if has_healer:
                            msg += f"\n请 {actor_name(event.target_id)} 等待奶妈救援"
                        elif has_other:
                            msg += f"\n请 {actor_name(event.target_id)} 等待救援"
                        else:
                            msg += f"\n躺着吧你 {actor_name(event.target_id)}"
                    self.output(msg, 'death_count_swift')
                    self.last_death_count = time() + 0.3

    def process_command(self, args):
        try:
            msg = self._process_command(args)
            self.storage.save()
            if msg is not None:
                api.Magic.echo_msg(msg)
        except Exception as e:
            api.Magic.echo_msg(e)

    def _process_command(self, args):
        if len(args) < 2:
            return str(self.storage.data['config'])
        key, value = args
        value = value.lower()
        if value == 'disable' or value == 'd':
            new = DISABLE
        elif value == 'echo' or value == 'e':
            new = ECHO
        elif value == 'party' or value == 'p':
            new = PARTY
        else:
            new = int(value)
        if key == 'all':
            for k in self.storage.data['config'].keys():
                self.storage.data['config'][k] = new
            return str(self.storage.data['config'])
        else:
            old = self.storage.data['config'].get(key)
            self.storage.data['config'][key] = new
            return f"{old} => {new}"
