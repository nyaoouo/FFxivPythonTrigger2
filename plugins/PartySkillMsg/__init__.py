from functools import lru_cache
from random import choice
from FFxivPythonTrigger import *

command = "@psm"


@lru_cache
def actor_name(actor_id):
    if actor_id == 0xe0000000: return '-'
    actor = api.XivMemory.actor_table.get_actor_by_id(actor_id)
    if actor is None: return f"unk_{actor_id:x}"
    return actor.Name


def is_in_party():
    return api.XivMemory.party.main_size > 1


class PartySkillMag(PluginBase):
    name = "PartySkillMag"
    save_when_unload = False

    def __init__(self):
        super().__init__()
        self.storage.data.setdefault('cast', dict())
        self.storage.data.setdefault('use', dict())
        self.storage.save()
        self.register_event('network/action_effect', self.action_effect)
        self.register_event('network/actor_cast', self.action_cast)
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)

    def action_effect(self, event):
        if event.source_id != api.XivMemory.player_info.id or event.action_type != "action": return
        key = str(event.action_id)
        if key not in self.storage.data['use']: return
        mode = "/p " if is_in_party() else "/e "
        targets = "、".join([actor_name(i) for i in event.targets.keys()])
        api.Magic.macro_command(mode + choice(self.storage.data['use'][key]).format(
            t=targets,
            target=targets,
            me=api.XivMemory.actor_table.get_me().Name,
        ))

    def action_cast(self, event):
        if event.source_id != api.XivMemory.player_info.id: return
        key = str(event.action_id)
        if key not in self.storage.data['cast']: return
        mode = "/p " if is_in_party() else "/e "
        api.Magic.macro_command(mode + choice(self.storage.data['cast'][key]).format(
            t=actor_name(event.target_id),
            target=actor_name(event.target_id),
            me=api.XivMemory.actor_table.get_me().Name,
        ))

    def process_command(self, args):
        try:
            msg = self._process_command(args)
            if msg is not None:
                api.Magic.echo_msg(msg)
        except Exception as e:
            api.Magic.echo_msg(e)

    def _process_command(self, args):
        if args[0] == "load":
            self.storage.load()
            return "load"
        else:
            return f"unknown args [{args[0]}]"
