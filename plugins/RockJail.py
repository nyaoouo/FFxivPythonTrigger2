from FFxivPythonTrigger import *

command = "@rj"

skills = {11115, 11116}
test_skills = {11115, 11116, 137}

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
        self.test_mode = False
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)

    def action_effect(self, evt):
        if evt.action_id not in (test_skills if self.test_mode else skills) or evt.action_type != "action":
            return
        with self.lock:
            if self.list and self.last_record_time < time() - (5 if self.test_mode else 1):
                self.list.clear()
            self.last_record_time = time()
            for t_id in evt.targets.keys():
                target = api.XivMemory.actor_table.get_actor_by_id(t_id)
                if target is None:
                    self.logger.error(f"an target with id:{hex(t_id)[2:]} is not found")
                    continue
                self.list.append((target.Name, target.job.raw_value, t_id))
            if len(self.list) >= 3:
                data = sorted(self.list, key=lambda x: order[x[1]])
                for i, t in enumerate(data): api.Markings.mark_actor(f'attack{i + 1}', t[2])
                mode = 'p' if len(list(api.XivMemory.party.main_party())) > 1 else 'e'
                api.Magic.macro_command(f"""/{mode} 石牢顺序：
\ue090：{jobs[data[0][1]]}｛{data[0][0]}｝
\ue091：{jobs[data[1][1]]}｛{data[1][0]}｝
\ue092：{jobs[data[2][1]]}｛{data[2][0]}｝
<se.6>""")

    def process_command(self, args):
        try:
            msg = self._process_command(args)
            if msg is not None:
                api.Magic.echo_msg(msg)
        except Exception as e:
            api.Magic.echo_msg(e)

    def _process_command(self, args):
        if args:
            if args[0] == "e":
                self.test_mode = True
            elif args[0] == "d":
                self.test_mode = False
            elif args[0]=="order":
                mode = 'p' if len(list(api.XivMemory.party.main_party())) > 1 else 'e'
                msg='\n'.join([f"{i+1}:{n}" for i,n in enumerate(jobs_order)])
                api.Magic.macro_command(f"""/{mode} 默认顺序：\n{msg}\n<se.6>""")
                return
            else:
                return f"[{args[0]}] is an invalid argument"
        else:
            self.test_mode = not self.test_mode
        return f"test:{self.test_mode}"
