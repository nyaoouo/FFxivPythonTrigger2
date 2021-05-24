import sqlite3

from FFxivPythonTrigger import *
from .DbCreator import get_con
from time import time

insert_ability = """
INSERT INTO `AbilityEvent`
(`timestamp`,`source_id`,`target_id`,`ability_id`,`type`,`param`)
VALUES (?,?,?,?,?,?)
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
select_max_timestamp = "SELECT Max(`timestamp`) FROM `AbilityEvent`"

owners = dict()


class CombatMonitor(PluginBase):
    name = "Combat Monitor"

    def __init__(self):
        super().__init__()
        # self.conn = get_con(self.storage.path / 'data.db')
        self.conn = get_con()
        self.conn_lock = Lock()
        self.register_event('network/action_effect', self.ability_insert)
        self.register_event('network/actor_control/dot', self.dot_insert)
        self.register_event('network/actor_control/hot', self.hot_insert)
        self.register_api('CombatMonitor', type('obj', (object,), {
            'actor_dps': self.actor_dps,
            'actor_tdps': self.actor_tdps,
        }))

    def save_db(self):
        with self.conn_lock:
            backup_conn = sqlite3.connect(self.storage.path / f'data_{int(time())}.db')
            self.conn.backup(backup_conn)
            backup_conn.close()
            self.conn.close()
            self.conn = get_con()

    def _onunload(self):
        self.save_db()
        self.conn.close()

    def ability_insert(self, evt):
        if evt.action_type == 'action':
            timestamp = int(evt.time.timestamp() * 1000)
            if evt.source_id not in owners:
                actor = api.XivMemory.actor_table.get_actor_by_id(evt.source_id)
                if actor is not None and actor.ownerId and actor.ownerId != 0xe0000000:
                    owners[evt.source_id] = actor.ownerId
                else:
                    owners[evt.source_id] = evt.source_id
            source = owners[evt.source_id]
            with self.conn_lock:
                c = self.conn.cursor()
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
                        c.execute(insert_ability, (timestamp, source, target_id, evt.action_id, action_type, effect.param))
                        record_id = c.lastrowid
                        for tag in temp:
                            c.execute(insert_ability_tag, (record_id, tag))
                self.conn.commit()

    def dot_insert(self, evt):
        data = (int(evt.time.timestamp() * 1000), None, evt.target_id, None, 'dot', evt.damage)
        with self.conn_lock:
            self.conn.cursor().execute(insert_ability, data)
            self.conn.commit()

    def hot_insert(self, evt):
        data = (int(evt.time.timestamp() * 1000), None, evt.target_id, None, 'hot', evt.damage)
        with self.conn_lock:
            self.conn.cursor().execute(insert_ability, data)
            self.conn.commit()

    def get_period(self, period_sec: float, till: int = None):
        if till is None:
            till = self.conn.execute(select_max_timestamp).fetchone()[0] or period_sec * 1000
        end_time = till
        return int(end_time - (period_sec * 1000)), till

    def actor_dps(self, source_id, period_sec=60, till: int = None):
        with self.conn_lock:
            data = self.conn.execute(select_damage_from, (source_id, *self.get_period(period_sec, till))).fetchone()
        return data[0] // max((data[2] - data[1]) / 1000, 1) if data[1] is not None else 0

    def actor_tdps(self, target_id, period_sec=60, till: int = None):
        with self.conn_lock:
            data = self.conn.execute(select_taken_damage_from, (target_id, *self.get_period(period_sec, till))).fetchone()
        return data[0] // max((data[2] - data[1]) / 1000, 1) if data[1] is not None else 0
