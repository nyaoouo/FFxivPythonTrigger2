from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger import FFxiv_Version
from ..Structs import SendNetworkEventBase, ServerMessageHeader, header_size
from . import Ping, PositionSet, PositionAdjust, EventStart, EventFinish, EventAction, ClientTrigger

from .Opcodes import opcodes

_logger = Logger("XivNetwork/SendProcessors")

_processors = {
    'Ping': Ping.get_event,
    "UpdatePositionHandler": PositionSet.get_event,
    "UpdatePositionInstance": PositionAdjust.get_event,
    "EventStart": EventStart.get_event,
    "EventFinish": EventFinish.get_event,
    "EventAction": EventAction.get_event,
    "ClientTrigger": ClientTrigger.get_event,
}


class UndefinedSend(SendNetworkEventBase):
    def __init__(self, msg_time, raw_msg):
        self.header = ServerMessageHeader.from_buffer(raw_msg)
        super().__init__(msg_time, raw_msg[header_size:])

    def text(self):
        return f"opcode:{self.header.msg_type} len:{len(self.raw_msg)}"


processors = dict()

_undefined_evt_class = dict()
version_opcodes = opcodes.setdefault(FFxiv_Version, dict())

for key, opcode in version_opcodes.items():
    if key not in _processors:
        _logger.debug(f"load send opcode of [{key}]({hex(opcode)}) - no processor defined")
        processors[opcode] = type(f'SendUndefined_{key}', (UndefinedSend,), {
            'id': f"network/undefined_send/{key}",
            'name': f"network undefined send - {key}",
        })
    else:
        _logger.debug(f"load send opcode of [{key}]({hex(opcode)})")
        processors[opcode] = _processors[key]
