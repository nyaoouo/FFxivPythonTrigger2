from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger import FFxiv_Version
from ..Structs import SendNetworkEventBase
from . import Ping, PositionSet, PositionAdjust

from .Opcodes import opcodes

_logger = Logger("XivNetwork/SendProcessors")

_processors = {
    'Ping': Ping.get_event,
    "UpdatePositionHandler": PositionSet.get_event,
    "UpdatePositionInstance": PositionAdjust.get_event,
}

processors = dict()

_undefined_evt_class = dict()
_opcodes = opcodes.setdefault(FFxiv_Version, dict())

for key, opcode in _opcodes.items():
    if key not in _processors:
        _logger.debug(f"load opcode of [{key}]({hex(opcode)}) - no processor defined")
        processors[opcode] = type(f'SendUndefined_{key}', (SendNetworkEventBase,), {
            'id': f"network/undefined_send/{key}",
            'name': f"network undefined send - {key}",
        })
    else:
        _logger.debug(f"load opcode of [{key}]({hex(opcode)})")
        processors[opcode] = _processors[key]
