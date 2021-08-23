from functools import cache
from json import dumps
from FFxivPythonTrigger import *
from FFxivPythonTrigger.SaintCoinach import realm
from .DbCreator import *
from .Definition import ability_damage, dot_damage

use_ui = True
if use_ui:
    from PyQt5.QtCore import QTimer, QUrl
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from FFxivPythonTrigger.QT import FloatWidget, ui_loop_exec

BREAK_TIME = 30
UPDATE_PERIOD = 0.1
MAX_TIME = 1e+99

owners = dict()

web_path = str(Path(__file__).parent / 'dist' / 'index.html')

status_sheet = realm.game_data.get_sheet('Status')


@cache
def status_name(status_id):
    if not status_id: return
    return status_sheet[status_id]['Name']


class CombatMonitor(PluginBase):
    name = "Combat Monitor"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/CombatMonitor'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super().__init__()

        # self.conn = get_con(self.storage.path / 'data.db')
        if use_ui:
            class DpsWindow(FloatWidget):
                allow_frameless = True

                def __init__(self):
                    super().__init__()
                    self.setWindowTitle("Dps")
                    self.browser = QWebEngineView()
                    self.browser.load(QUrl.fromLocalFile(web_path))
                    # self.browser.load(QUrl("http://localhost:8080"))
                    _layout = QVBoxLayout(self)
                    _layout.addWidget(self.browser)
                    self.setLayout(_layout)

                    self.last_update = 0

                    self.timer = QTimer()
                    self.timer.setInterval(UPDATE_PERIOD * 2000)
                    self.timer.timeout.connect(self.update)
                    self.timer.start()

                def update(_self):
                    try:
                        me = api.XivMemory.actor_table.get_me()
                        if me is None or _self.last_update > self.last_record_time: return
                        party = [actor for actor in api.XivMemory.party.main_party()]
                        if not party: party = [me]
                        data = [{
                            'job': a.job.name,
                            'name': a.Name,
                            'dps': self.actor_dps(a.id, 0),
                            'dps_m': self.actor_dps(a.id, 60),
                            # 'dps_sd': self.actor_sim_dot_dps(a.id, 0),
                            'dmg': self.actor_dmg(a.id, 0),
                            # 'dmg_sd': self.actor_sim_dot_dmg(a.id, 0),
                            # 'dmg_sd_g': '、'.join([
                            #     f"{status_name(e_id)}({dmg:,})"
                            #     for e_id, dmg in self.actor_sim_dot_dmg_group(a.id, 0)
                            # ]),
                            'death': self.dead_record.setdefault(a.id, 0),
                        } for a in party]
                        lb_d = self.actor_dps(-1, 0)
                        if lb_d:
                            data.append({
                                'job': 'LB',
                                'name': 'Limit Break',
                                'dps': self.actor_dps(-1, 0),
                                'dps_m': self.actor_dps(-1, 60),
                            })
                        script = f"window.set_data({self.min_record_time},{self.last_record_time}," \
                                 f"\"{api.XivMemory.zone_name}({api.XivMemory.zone_id})\",{dumps(data)})"
                        _self.browser.page().runJavaScript(script)
                        _self.last_update = time() * 1000
                    except:
                        self.logger.error(format_exc())

            self.dps_window: DpsWindow = ui_loop_exec(DpsWindow)

        self.conn = get_con()
        self.conn_lock = Lock()
        self.id_lock = Lock()
        self.queue_lock = Lock()
        self.time_set_lock = Lock()
        self.insert_lock = Lock()
        self.register_event('network/action_effect', self.ability_insert)
        self.register_event('network/actor_control/dot', self.dot_hot_insert)
        self.register_event('network/actor_control/hot', self.dot_hot_insert)
        self.register_event('network/actor_control/death', self.player_dead)
        self.register_event('network/actor_control/director_update/initial_commence', self.set_min_time)
        self.register_api('CombatMonitor', type('obj', (object,), {
            'actor_dps': self.actor_dps,
            'actor_tdps': self.actor_tdps,
        }))
        frame_inject.register_continue_call(self.continue_work)
        self.ability_data = list()
        self.ability_tag_data = list()
        self.last_id = 0
        self.last_update = perf_counter()
        self._min_record_time = MAX_TIME
        self.last_record_time = self._last_record_time = self.min_record_time = 0
        self.dot_k_values = dict()
        self.dot_values = dict()
        self.dead_record = dict()

    def _start(self):
        if use_ui: ui_loop_exec(self.dps_window.show)
        pass

    def set_min_time(self, evt):
        self.logger.debug("resetting min time")
        self.last_record_time = self._last_record_time = self.min_record_time = 0

    def data_insert(self):
        if not self.insert_lock.acquire(blocking=False):
            return
        try:
            if not self.ability_data: return

            with self.time_set_lock:
                if self._min_record_time < MAX_TIME and self._min_record_time - (
                        BREAK_TIME * 1000) > self.last_record_time or not self.min_record_time:
                    self.min_record_time = self._min_record_time
                self._min_record_time = MAX_TIME
                self.last_record_time = self._last_record_time
            with self.queue_lock:
                ability_data = self.ability_data.copy()
                ability_tag_data = self.ability_tag_data.copy()
                self.ability_data.clear()
                self.ability_tag_data.clear()
            with self.conn_lock:
                c = self.conn.cursor()
                c.executemany(insert_ability, ability_data)
                c.executemany(insert_ability_tag, ability_tag_data)
                self.conn.commit()
                self._actor_dmg.cache_clear()
                self._actor_sim_dot_dmg.cache_clear()
                self._actor_taken_dmg.cache_clear()
                self._actor_sim_dot_dmg_group.cache_clear()
        finally:
            self.insert_lock.release()

    def continue_work(self):
        current = perf_counter()
        if current - self.last_update < UPDATE_PERIOD: return
        self.last_update = current
        self.create_mission(self.data_insert)

    def save_db(self):
        with self.conn_lock:
            save_path = self.storage.path / f'data_{int(time())}.db'
            backup_conn = sqlite3.connect(save_path)
            self.conn.backup(backup_conn)
            backup_conn.close()
            self.logger.debug(f"backup database at {save_path}")
            self.conn.close()
            self.conn = get_con()

    def _onunload(self):
        if use_ui: ui_loop_exec(self.dps_window.full_close)
        frame_inject.unregister_continue_call(self.continue_work)
        self.save_db()
        self.conn.close()

    def get_new_ability_id(self):
        with self.id_lock:
            d_id = self.last_id
            self.last_id += 1
        return d_id

    def set_dot_value(self, target_id, source_id, dot_id):
        if dot_id not in dot_damage or source_id not in self.dot_k_values: return False
        self.dot_values[(target_id, source_id, dot_id)] = self.dot_k_values[source_id] * dot_damage[dot_id]
        return True

    def get_dot_value(self, target_id, actor_id, dot_id):
        if dot_id not in dot_damage: return 0
        k = (target_id, actor_id, dot_id)
        if k not in self.dot_values and not self.set_dot_value(target_id, actor_id, dot_id):
            d = list(self.dot_k_values.values())
            if not d: return dot_damage[dot_id]
            return sum(d) / len(d) * dot_damage[dot_id]
        return self.dot_values[k]

    def player_dead(self, evt):
        if evt.target_id not in self.dead_record:
            self.dead_record[evt.target_id] = 1
        else:
            self.dead_record[evt.target_id] += 1

    def ability_insert(self, evt):
        if evt.action_type != 'action': return
        timestamp = int(evt.time.timestamp() * 1000)
        if evt.source_id not in owners:
            actor = api.XivMemory.actor_table.get_actor_by_id(evt.source_id)
            if actor is not None and actor.ownerId and actor.ownerId != 0xe0000000:
                owners[evt.source_id] = actor.ownerId
            else:
                owners[evt.source_id] = evt.source_id
        source = owners[evt.source_id]
        ability_data = list()
        ability_tag_data = list()
        is_set = False
        for target_id, effects in evt.targets.items():
            for effect in effects:
                temp = effect.tags.copy()
                if 'ability' in temp:
                    if source >= 0 and 'limit_break' in temp: source = -1
                    if not is_set:
                        is_set = True
                        with self.time_set_lock:
                            self._min_record_time = min(timestamp, self._min_record_time)
                            self._last_record_time = max(timestamp, self._last_record_time)
                    action_type = 'damage'
                    temp.remove('ability')
                elif 'healing' in temp:
                    action_type = 'healing'
                    temp.remove('healing')
                elif 'buff' in temp:
                    action_type = 'buff'
                    temp.remove('buff')
                else:
                    continue
                d_id = self.get_new_ability_id()
                ability_data.append((d_id, timestamp, source, target_id, evt.action_id, action_type, effect.param))
                ability_tag_data += [(d_id, tag) for tag in temp]
                if target_id < 0x20000000:
                    if action_type == 'damage' and evt.action_id in ability_damage:
                        dmg = effect.param
                        if 'critical' in effect.tags: dmg /= 1.4
                        if 'direct' in effect.tags: dmg /= 1.25
                        self.dot_k_values[source] = dmg / ability_damage[evt.action_id]
                    elif action_type == 'buff' and "to_target" in effect.tags and effect.param in dot_damage:
                        self.set_dot_value(target_id, source, effect.param)
        with self.queue_lock:
            self.ability_data += ability_data
            self.ability_tag_data += ability_tag_data

    def dot_hot_insert(self, evt):
        timestamp = int(evt.time.timestamp() * 1000)
        if evt.is_dot:
            with self.time_set_lock:
                self._min_record_time = min(timestamp, self._min_record_time)
                self._last_record_time = max(timestamp, self._last_record_time)
            e_type = 'dot'
        else:
            e_type = 'hot'
        b_id = evt.source_buff_id if evt.source_buff_id else None
        s_id = evt.source_id if evt.source_buff_id else None
        with self.queue_lock:
            self.ability_data.append((self.get_new_ability_id(), timestamp, s_id, evt.target_id, b_id, e_type, evt.damage))
        if not b_id:
            if evt.is_dot:
                t_id = evt.target_id
                t = api.XivMemory.actor_table.get_actor_by_id(t_id)
                if t is None: return
                d_effects = [(k, e.actorId) for k, e in t.effects.get_dict().items() if k in dot_damage]
                if not d_effects: return
                d_effects = [(self.get_dot_value(t_id, x[1], x[0]), x[1], x[0]) for x in d_effects]
                s_d = evt.damage / sum([x[0] for x in d_effects])
                for p_d, s_id, e_id in d_effects:
                    self.ability_data.append((self.get_new_ability_id(), timestamp, s_id, t_id, e_id, "dot_sim", round(s_d * p_d)))

    def get_period(self, period_sec: float, till: int = None):
        if till is None: till = self.last_record_time
        if not period_sec: return self.min_record_time, till
        return max(self.min_record_time, int(till - (period_sec * 1000))), till

    def actor_dmg(self, source_id, period_sec=60, till: int = None):
        return self._actor_dmg(source_id, *self.get_period(period_sec, till))

    def actor_dps(self, source_id, period_sec=60, till: int = None):
        start_time, end_time = self.get_period(period_sec, till)
        dmg = self._actor_dmg(source_id, start_time, end_time)
        return dmg // max((end_time - start_time) / 1000, 1) if dmg else 0

    def actor_sim_dot_dmg(self, source_id, period_sec=60, till: int = None):
        return self._actor_sim_dot_dmg(source_id, *self.get_period(period_sec, till))

    def actor_sim_dot_dmg_group(self, source_id, period_sec=60, till: int = None):
        return self._actor_sim_dot_dmg_group(source_id, *self.get_period(period_sec, till))

    def actor_sim_dot_dps(self, source_id, period_sec=60, till: int = None):
        start_time, end_time = self.get_period(period_sec, till)
        dmg = self._actor_sim_dot_dmg(source_id, start_time, end_time)
        return dmg // max((end_time - start_time) / 1000, 1) if dmg else 0

    def actor_tdps(self, target_id, period_sec=60, till: int = None):
        start_time, end_time = self.get_period(period_sec, till)
        tdmg = self._actor_taken_dmg(target_id, start_time, end_time)
        return tdmg // max((end_time - start_time) / 1000, 1) if tdmg else 0

    @cache
    def _actor_taken_dmg(self, source_id, start_time: int, end_time: int):
        with self.conn_lock:
            data = self.conn.execute(select_taken_damage_from, (source_id, start_time, end_time)).fetchone()
        return data[0] if data[0] is not None else 0

    @cache
    def _actor_sim_dot_dmg(self, source_id, start_time: int, end_time: int):
        with self.conn_lock:
            data = self.conn.execute(select_sim_dot_damage_from, (source_id, start_time, end_time)).fetchone()
        return data[0] if data[0] is not None else 0

    @cache
    def _actor_sim_dot_dmg_group(self, source_id, start_time: int, end_time: int):
        with self.conn_lock:
            data = self.conn.execute(select_sim_dot_damage_group_from, (source_id, start_time, end_time)).fetchall()
        return [(row[0], row[1]) for row in data]

    @cache
    def _actor_dmg(self, source_id, start_time: int, end_time: int):
        with self.conn_lock:
            data = self.conn.execute(select_damage_from, (source_id, start_time, end_time)).fetchone()
        return data[0] if data[0] is not None else 0
