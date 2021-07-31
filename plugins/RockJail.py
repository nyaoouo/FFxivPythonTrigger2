from FFxivPythonTrigger import *

skills = {11115, 11116}

jobs = {
    19: '骑士',  # 骑士PLD
    20: '武僧',  # 武僧MNK
    21: '战士',  # 战士WAR
    22: '龙骑',  # 龙骑士DRG
    23: '诗人',  # 吟游诗人BRD
    24: '白魔',  # 白魔法师WHM
    25: '黑魔',  # 黑魔法师BLM
    27: '召唤',  # 召唤师SMN
    28: '学者',  # 学者SCH
    30: '忍者',  # 忍者NIN
    31: '机工',  # 机工士MCH
    32: '黑骑',  # 暗黑骑士DRK
    33: '占星',  # 占星术士AST
    34: '武士',  # 武士SAM
    35: '赤魔',  # 赤魔法师RDM
    37: '绝枪',  # 绝枪战士GNB
    38: '舞者'  # 舞者DNC
}

jobs_order = [
    '黑骑',
    '战士',
    '绝枪',
    '骑士',
    '武士',
    '武僧',
    '忍者',
    '龙骑',
    '机工',
    '舞者',
    '诗人',
    '黑魔',
    '赤魔',
    '召唤',
    '白魔',
    '占星',
    '学者',
]

jobs_k = {v: k for k, v in jobs.items()}
order = {k: jobs_order.index(v) for k, v in jobs.items()}


class RockJail(PluginBase):
    name = "RockJail"

    def __init__(self):
        super().__init__()
        self.register_event('network/action_effect', self.action_effect)
        self.list = []
        self.last_record_time = 0
        self.lock = Lock()

    def action_effect(self, evt):
        if evt.action_id not in skills or evt.action_type != "action":
            return
        with self.lock:
            if self.list and self.last_record_time < time() - 1:
                self.list.clear()
            self.last_record_time = time()
            for t_id in evt.targets.keys():
                target = api.XivMemory.actor_table.get_actor_by_id(t_id)
                if target is None:
                    self.logger.error(f"an target with id:{hex(t_id)[2:]} is not found")
                    continue
                self.list.append((target.Name, target.job.raw_value))
            if len(self.list) >= 3:
                data = sorted(self.list, key=lambda x: order[x[1]])
                msg = '》'.join([f"{jobs[job_value]}({name[0]})" for name, job_value in data])
                api.Magic.macro_command(f"/e 泰坦》{msg}》地雷 <se.6>")
