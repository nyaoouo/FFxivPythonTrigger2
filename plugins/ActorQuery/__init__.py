from FFxivPythonTrigger import PluginBase, api

command = "@aq"


class ActorQuery(PluginBase):
    name = "Actor Query"

    def __init__(self):
        super().__init__()
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)

    def process_command(self, args):
        try:
            args = ' '.join(args).split(';')
            if len(args) > 1:
                select, query = args[0].split(','), ';'.join(args[1:])
            else:
                select, query = ['Name'], args[0]
            select = select if select else ['Name']
            data = [actor for actor in api.XivMemory.actor_table.get_item() if eval(query)]
            data = [" ".join([str(getattr(d, i)) for i in select]) for d in data]
            api.Magic.echo_msg("found %s actor:" % len(data))
            for line in data:
                api.Magic.echo_msg(line)
        except Exception as e:
            api.Magic.echo_msg("error:" + str(e))
