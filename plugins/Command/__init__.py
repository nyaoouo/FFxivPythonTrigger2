from FFxivPythonTrigger import *
import traceback

from FFxivPythonTrigger.memory import write_ubytes

"""
provide a service process echo message as commands
api:    command
            register(command: str, callback:callable)
            unregister(command:str)

privide some basic control commands
command:    @fpt
format:     /e @fpt [func] [args]...
functions (*[arg] is optional args):
    [list]:     list installed plugins
    [close]:    shut down the FFxiv Python trigger (recommend!!!!)
    [raise]:    try to raise an exception
    [log]:      log something
                format: /e @fpt log [message]
    [unload]:   unload (or named as disabled) an module
                format: /e @fpt unload [module_name]
    [reload]:   reload (or named as load) an module
                format: /e @fpt reload [module_name]
"""


class CommandPlugin(PluginBase):
    name = "command controller"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/Command'
    hash_path = os.path.dirname(__file__)

    def FptManager(self, args):
        if args[0] == 'close':
            close()
        elif args[0] == 'raise':
            raise Exception("111aw")
        elif args[0] == 'unload':
            unload_module(args[1])
        elif args[0] == 'reload':
            reload_module(args[1])
        elif args[0] == 'list':
            api.Magic.echo_msg("\n".join(list_plugin_names()))
        elif args[0] == 'log':
            self.logger.info(" ".join(args[1:]))
        elif args[0] == 'eval':
            exec(" ".join(args[1:]))
        elif args[0] == 'kill!':
            write_ubytes(frame_inject.address, bytearray(b'\x90' * 99))

    def deal_chat_log(self, event):
        if event.channel_id == 56:
            args = event.message.split(' ')
            if args[0] in self.commands:
                self.logger.debug(event.message)
                try:
                    self.commands[args[0]](args[1:])
                except Exception:
                    self.logger.error('exception occurred:\n{}'.format(traceback.format_exc()))

    def register(self, command: str, callback):
        if ' ' in command:
            raise Exception("Command should not contain blanks")
        if command in self.commands:
            raise Exception("Command %s already exists" % command)
        self.commands[command] = callback

    def unregister(self, command):
        if command in self.commands:
            del self.commands[command]

    def __init__(self):
        super(CommandPlugin, self).__init__()

        class CommandApi:
            register = self.register
            unregister = self.unregister

        self.commands = dict()
        self.register_event("log_event", self.deal_chat_log)
        self.register_api('command', CommandApi())
        self.register('@fpt', self.FptManager)
