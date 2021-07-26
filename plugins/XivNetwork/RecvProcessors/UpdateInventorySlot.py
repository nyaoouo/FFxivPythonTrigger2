from ctypes import *
from functools import cached_property

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase, header_size


class ServerUpdateInventorySlot(OffsetStruct({
    'index': c_uint,
    'unk0': c_uint,
    'container_id': c_ushort,
    'slot': c_ushort,
    'count': c_uint,
    'item_id': c_uint,
    'reserved_flag': c_uint,
    'signature_id': c_ulonglong,
    'quality': c_ubyte,
    'attribute2': c_ubyte,
    'condition': c_ushort,
    'spiritbond': c_ushort,
    'stain': c_ushort,
    'glamour_catalog_id': c_ushort,
    'unk6': c_ushort,
    'materia1': c_ushort,
    'materia2': c_ushort,
    'materia3': c_ushort,
    'materia4': c_ushort,
    'materia5': c_ushort,
    'materia1_tier': c_ubyte,
    'materia2_tier': c_ubyte,
    'materia3_tier': c_ubyte,
    'materia4_tier': c_ubyte,
    'materia5_tier': c_ubyte,
    'unk10': c_ubyte,
    'unk11': c_uint,
}, 0x40)):pass


_logger = Logger("XivNetwork/ProcessServerUpdateInventorySlot")
size = sizeof(ServerUpdateInventorySlot)
item_sheet = realm.game_data.get_sheet('Item')

class ServerUpdateInventorySlotEvent(RecvNetworkEventBase):
    id = "network/update_inventory_slot"
    name = "network recv update inventory slot"

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
    return ServerUpdateInventorySlotEvent(msg_time, ServerUpdateInventorySlot.from_buffer(raw_msg[header_size:]))
