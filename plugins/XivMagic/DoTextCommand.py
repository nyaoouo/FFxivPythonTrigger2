from FFxivPythonTrigger import frame_inject
from FFxivPythonTrigger.memory import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, PointerStruct
from .AddressManager import do_text_command_addr, text_command_ui_module_ptr_addr
from threading import Lock

_lock = Lock()

TextCommandStruct = OffsetStruct({
    "cmd": c_void_p,
    "t1": c_longlong,
    "tLength": c_longlong,
    "t3": c_longlong,
}, full_size=400)

_ = ida_sig_to_pattern
ui_module = memory.read_memory(PointerStruct(c_void_p, 0), text_command_ui_module_ptr_addr)
_text_command_func = CFUNCTYPE(c_int64, c_void_p, c_void_p, c_int64, c_char)(do_text_command_addr)


def _do_text_command(command: str) -> int:
    encoded_command = command.encode('utf-8')
    cmd_size = len(encoded_command)
    cmd = OffsetStruct({"cmd": c_char * cmd_size}, full_size=cmd_size + 30)(cmd=encoded_command)
    arg = TextCommandStruct(cmd=addressof(cmd), t1=64, tLength=cmd_size + 1, t3=0)
    return _text_command_func(ui_module.value, addressof(arg), 0, 0)


def do_text_command(command: str):
    frame_inject.register_once_call(_do_text_command, command)
