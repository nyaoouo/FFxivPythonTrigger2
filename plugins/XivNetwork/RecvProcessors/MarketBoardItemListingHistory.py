from ctypes import *
from functools import cached_property

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase


class MarketBoardHistoryItemEntry(OffsetStruct({
    'selling_price': c_uint,
    'purchase_time': c_uint,
    'item_count': c_uint,
    'is_hq': c_bool,
    'unk1': c_ubyte,
    'is_mannequin': c_bool,
    '_buyer_name': c_ubyte * 33,
    'item_id': c_uint,
}, extra_properties=['buyer_name'])):
    @property
    def buyer_name(self):
        return bytes(self._buyer_name).decode('utf-8').rstrip("\x00")

    @cached_property
    def item(self):
        if self.item_id:
            return item_sheet[self.item_id]


ServerMarketBoardItemListHistory = OffsetStruct({
    'item_id': c_uint,
    'item_id2': c_uint,
    'histories': MarketBoardHistoryItemEntry * 20,
},1048)

_logger = Logger("XivNetwork/ProcessMarketBoardItemList")
size = sizeof(ServerMarketBoardItemListHistory)
item_sheet = realm.game_data.get_sheet('Item')


class ServerMarketBoardItemListHistoryEvent(RecvNetworkEventBase):
    id = "network/recv_market_board_item_list_history"
    name = "network recv market board item list history"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.count = 0
        for item in self.raw_msg.histories:
            if item.item_id:
                self.count += 1
            else:
                break

    @cached_property
    def item(self):
        if self.raw_msg.item_id:
            return item_sheet[self.raw_msg.item_id]

    def text(self):
        return f"{self.item['Name']} x{self.count}"


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerMarketBoardItemListHistoryEvent(msg_time, header, ServerMarketBoardItemListHistory.from_buffer(raw_msg))
