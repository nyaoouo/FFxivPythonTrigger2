from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase, header_size


class ServerRetainerInformation(OffsetStruct({
    'unk0': c_ulonglong,
    'retainer_id': c_uint,
    'server_id': c_uint,
    'type': c_ubyte,
    'inventory_count': c_ubyte,
    'unk2': c_ushort,
    'gold': c_uint,
    'selling_count': c_ubyte,
    'market': c_ubyte,
    'class_job': c_ubyte,
    'level': c_ubyte,
    'sell_end_time': c_uint,
    'mission_id': c_uint,
    'adv_end_time': c_uint,
    'reserved': c_ubyte,
    '_name': c_char * 39,
}, 80, ['name'])):
    @property
    def name(self):
        return self._name.decode('utf-8', errors='ignore')


_logger = Logger("XivNetwork/ProcessServerRetainerInformation")
size = sizeof(ServerRetainerInformation)


class ServerRetainerInformationEvent(RecvNetworkEventBase):
    id = "network/recv_retainer_info"
    name = "network recv retainer info"

    def text(self):
        return f"{self.raw_msg.name} {hex(self.raw_msg.retainer_id)}/{hex(self.raw_msg.server_id)}" if self.raw_msg.reserved else 'n/a'


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerRetainerInformationEvent(msg_time, ServerRetainerInformation.from_buffer(raw_msg[header_size:]))
