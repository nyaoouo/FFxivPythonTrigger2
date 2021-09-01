from ctypes import *
from functools import cached_property

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase

ServerMarketBoardItemListCount = OffsetStruct({
    'item_id': c_uint,
    'item_count': (c_ubyte, 0xb),
}, 16)

_logger = Logger("XivNetwork/ProcessMarketBoardItemListCount")
size = sizeof(ServerMarketBoardItemListCount)
item_sheet = realm.game_data.get_sheet('Item')


class ServerMarketBoardItemListCountEvent(RecvNetworkEventBase):
    id = "network/recv_market_board_item_list_count"
    name = "network recv market board item list count"

    @cached_property
    def item(self):
        if self.raw_msg.item_id:
            return item_sheet[self.raw_msg.item_id]

    def text(self):
        return f"{self.item['Name']} x{self.raw_msg.item_count} "


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerMarketBoardItemListCountEvent(msg_time, header, ServerMarketBoardItemListCount.from_buffer(raw_msg))
