from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ctypes import *

InventoryItem = OffsetStruct({
    'page_type': (c_short, 0),
    'idx': (c_ubyte, 4),
    'id': (c_uint, 8),
    'count': (c_uint, 12),
    'collectability': (c_ushort, 16),
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
