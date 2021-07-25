from ctypes import *
from functools import cached_property

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase, header_size

class ServerCurrencyCrystalInfo(OffsetStruct({
    'container_sequence': c_uint,
    'container_id': c_ushort,
    'slot': c_ushort,
    'count': c_uint,
    'unk0': c_uint,
    'item_id': c_uint,
    'unk1': c_uint,
    'unk2': c_uint,
    'unk3': c_uint,
}, 32)):
    pass

_logger = Logger("XivNetwork/ProcessServerCurrencyCrystalInfo")
size = sizeof(ServerCurrencyCrystalInfo)
item_sheet = realm.game_data.get_sheet('Item')


class ServerCurrencyCrystalInfoEvent(RecvNetworkEventBase):
    id = "network/recv_currency_crystal_info"
    name = "network recv currency crystal info"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.container_id = self.raw_msg.container_id
        self.slot = self.raw_msg.slot
        self.count = self.raw_msg.count

    @cached_property
    def item(self):
        return item_sheet[self.raw_msg.item_id]

    def text(self):
        return f"{self.item['Name']} x{self.count} at container:{hex(self.container_id)} - slot:{self.slot}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerCurrencyCrystalInfoEvent(msg_time, ServerCurrencyCrystalInfo.from_buffer(raw_msg[header_size:]))
