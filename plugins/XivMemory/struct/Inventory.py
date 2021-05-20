from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ctypes import *

InventoryItem = OffsetStruct({
    'page_type': (c_short, 0x0),
    'idx': (c_short, 0x4),
    'id': (c_uint, 0x8),
    'count': (c_uint, 0xc),
    'collectability': (c_ushort, 0x10),
    'durability': (c_ushort, 0x12),
    'is_hq': (c_bool, 20)
}, full_size=56)


class InventoryPage(OffsetStruct({
    'page': POINTER(InventoryItem),
    'type': c_uint,
    'size': c_uint
}, full_size=24)):
    def get_items(self):
        if not self.page: return
        for i in range(self.size):
            yield self.page[i]


InventoryPageIdx = InventoryPage * 74
