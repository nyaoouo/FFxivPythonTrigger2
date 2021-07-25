from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import SendNetworkEventBase, header_size


class ClientTrigger(OffsetStruct({
    'param1': c_uint,
    'param2': c_uint,
    'param3': c_uint,
    'param4': c_uint,
    'param5': c_uint,
    'param6': c_uint,
    'param7': c_uint,
    'param8': c_uint,
}, 32)): pass


_logger = Logger("XivNetwork/ProcessClientTrigger")
size = sizeof(ClientTrigger)


class ClientTriggerEvent(SendNetworkEventBase):
    id = "network/send_client_trigger"
    name = "network send client trigger"

    def text(self):
        return '|'.join(hex(v)[2:] for v in self.raw_msg.get_data().values())


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ClientTriggerEvent(msg_time, ClientTrigger.from_buffer(raw_msg[header_size:]))
