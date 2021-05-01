from FFxivPythonTrigger.memory import scan_address, write_float, read_float,read_ulonglong
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger import PluginBase, api

"""
change the zoom value to let you see more
command:    @zoom
format:     /e @zoom [func] [args]...
functions (*[arg] is optional args):
    [get]:      get current zoom value
    [set]:      set current zoom value
                format: /e @zoom set [value(float) / "default"]
"""

command = "@zoom"

sig = "48 8d 1d ?? ?? ?? ?? 48 8b cb 41 8d 50 02"

default = 20


class ZoomPlugin(PluginBase):
    name = "Zoom"

    def __init__(self):
        super().__init__()
        addr_ptr = AddressManager(self.storage.data, self.logger).get("addr ptr", scan_address, sig, cmd_len=7)
        self.addr = read_ulonglong(addr_ptr)+284
        self.logger.debug("address read at %s"%hex(self.addr))
        self.storage.save()
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)

    def _start(self):
        write_float(self.addr, self.storage.data.setdefault("user_default",default))

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if arg[0] == "set":
                if arg[1] == 'default':
                    arg[1] = default
                else:
                    self.storage.data["user_default"] = float(arg[1])
                    self.storage.save()
                write_float(self.addr, float(arg[1]))
                return "set to %s" % arg[1]
            elif arg[0] == "get":
                return read_float(self.addr)
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            return str(e)
