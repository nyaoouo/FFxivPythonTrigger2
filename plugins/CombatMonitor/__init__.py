import sqlite3

import actor as actor
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGridLayout, QLabel

from FFxivPythonTrigger import *
from FFxivPythonTrigger.QT import FloatWidget, ui_loop_exec
from .DbCreator import get_con
from time import time, perf_counter

BREAK_TIME = 60
UPDATE_PERIOD = 0.1
MAX_TIME = 2000000000000

insert_ability = """
INSERT INTO `AbilityEvent`
(`id`,`timestamp`,`source_id`,`target_id`,`ability_id`,`type`,`param`)
VALUES (?,?,?,?,?,?,?)
"""
insert_ability_tag = """
INSERT INTO `AbilityTags`
(`ability_event_id`,`tag`)
VALUES (?,?);
"""
select_damage_from = """
SELECT SUM(`param`),MIN(`timestamp`),Max(`timestamp`)
FROM `AbilityEvent`
WHERE
    (`source_id` = ?) AND
    (`timestamp` BETWEEN ? AND ?) AND
    (`type` = 'damage');
"""
select_taken_damage_from = """
SELECT SUM(`param`),MIN(`timestamp`),Max(`timestamp`)
FROM `AbilityEvent`
WHERE
    (`target_id` = ?) AND
    (`timestamp` BETWEEN ? AND ?) AND
    (`type` = 'damage' OR `type` = 'dot');
"""

owners = dict()


class CombatMonitor(PluginBase):
    name = "Combat Monitor"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/CombatMonitor'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super().__init__()

        # self.conn = get_con(self.storage.path / 'data.db')

        class DpsWindow(FloatWidget):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Dps")
                self.label = QLabel('No Data')
                self.label.setFont(QFont('Times', 20))
                self.layout = QGridLayout()
                self.layout.addWidget(self.label)
                self.setLayout(self.layout)
                self.timer = QTimer()
                self.timer.setInterval(UPDATE_PERIOD * 1000)
                self.timer.timeout.connect(self.update)
                self.timer.start()

            def update(_self):
                me = api.XivMemory.actor_table.get_me()
                if me is None: return
                party = [actor for actor in api.XivMemory.party.main_party()]
                if not party: party = [me]
                data = [(a, self.actor_dps(a.id, 0)) for a in party]
                data.sort(key=lambda x: x[1], reverse=True)
                _self.label.setText("\n".join([f"{a.job.value()}\t{a.Name}\t{d}" for a, d in data]))

        self.conn = get_con()
        self.conn_lock = Lock()
        self.id_lock = Lock()
        self.queue_lock = Lock()
        self.time_set_lock = Lock()
        self.register_event('network/action_effect', self.ability_insert)
        self.register_event('network/actor_control/dot', self.dot_insert)
        self.register_event('network/actor_control/hot', self.hot_insert)
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
        self.last_record_time = self._last_record_time = self.min_record_time = int(time() * 1000)
        self.dps_cache = dict()
        self.tdps_cache = dict()
        self.dps_window: DpsWindow = ui_loop_exec(DpsWindow)

    def _start(self):
        ui_loop_exec(self.dps_window.show)

    def set_min_time(self, evt):
        self.last_record_time = self.min_record_time = int(time() * 1000)

    def continue_work(self):
        current = perf_counter()
        if current - self.last_update < UPDATE_PERIOD: return
        self.last_update = current
        if not self.ability_data: return

        with self.time_set_lock:
            if self._min_record_time < MAX_TIME and self._min_record_time - (BREAK_TIME * 1000) > self.last_record_time:
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
            self.dps_cache.clear()
            self.tdps_cache.clear()

    def save_db(self):
        with self.conn_lock:
            backup_conn = sqlite3.connect(self.storage.path / f'data_{int(time())}.db')
            self.conn.backup(backup_conn)
            backup_conn.close()
            self.conn.close()
            self.conn = get_con()

    def _onunload(self):
        ui_loop_exec(self.dps_window.full_close)
        frame_inject.unregister_continue_call(self.continue_work)
        self.save_db()
        self.conn.close()

    def get_new_ability_id(self):
        with self.id_lock:
            d_id = self.last_id
            self.last_id += 1
        return d_id

    def ability_insert(self, evt):
        if evt.action_type != 'action': return
        timestamp = int(evt.time.timestamp() * 1000)
        with self.time_set_lock:
            self._min_record_time = min(timestamp, self._min_record_time)
            self._last_record_time = max(timestamp, self._last_record_time)
        if evt.source_id not in owners:
            actor = api.XivMemory.actor_table.get_actor_by_id(evt.source_id)
            if actor is not None and actor.ownerId and actor.ownerId != 0xe0000000:
                owners[evt.source_id] = actor.ownerId
            else:
                owners[evt.source_id] = evt.source_id
        source = owners[evt.source_id]
        ability_data = list()
        ability_tag_data = list()
        for target_id, effects in evt.targets.items():
            for effect in effects:
                temp = effect.tags.copy()
                if 'ability' in temp:
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
        with self.queue_lock:
            self.ability_data += ability_data
            self.ability_tag_data += ability_tag_data

    def dot_insert(self, evt):
        timestamp = int(evt.time.timestamp() * 1000)
        with self.time_set_lock:
            self._min_record_time = min(timestamp, self._min_record_time)
            self._last_record_time = max(timestamp, self._last_record_time)
        with self.queue_lock:
            self.ability_data.append((self.get_new_ability_id(), timestamp, None, evt.target_id, None, 'dot', evt.damage))

    def hot_insert(self, evt):
        timestamp = int(evt.time.timestamp() * 1000)
        with self.time_set_lock:
            self._min_record_time = min(timestamp, self._min_record_time)
            self._last_record_time = max(timestamp, self._last_record_time)
        with self.queue_lock:
            self.ability_data.append((self.get_new_ability_id(), timestamp, None, evt.target_id, None, 'hot', evt.damage))

    def get_period(self, period_sec: float, till: int = None):
        if till is None: till = self.last_record_time
        if not period_sec: return self.min_record_time, till
        return max(self.min_record_time, int(till - (period_sec * 1000))), till

    def actor_dps(self, source_id, period_sec=60, till: int = None):
        key = (source_id, *self.get_period(period_sec, till))
        if key not in self.dps_cache: self.dps_cache[key] = self._actor_dps(*key)
        return self.dps_cache[key]

    def actor_tdps(self, target_id, period_sec=60, till: int = None):
        key = (target_id, *self.get_period(period_sec, till))
        if key not in self.tdps_cache: self.tdps_cache[key] = self._actor_tdps(*key)
        return self.tdps_cache[key]

    def _actor_dps(self, source_id, period_sec, till: int):
        with self.conn_lock:
            data = self.conn.execute(select_damage_from, (source_id, *self.get_period(period_sec, till))).fetchone()
        return data[0] // max((data[2] - data[1]) / 1000, 1) if data[1] is not None else 0

    def _actor_tdps(self, target_id, period_sec, till: int):
        with self.conn_lock:
            data = self.conn.execute(select_taken_damage_from, (target_id, *self.get_period(period_sec, till))).fetchone()
        return data[0] // max((data[2] - data[1]) / 1000, 1) if data[1] is not None else 0
