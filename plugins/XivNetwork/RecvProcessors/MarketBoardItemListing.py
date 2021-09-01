from ctypes import *
from functools import cached_property

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase


class MarketBoardItemEntry(OffsetStruct({
    'listing_id': c_uint64,
    'retainer_id': c_uint64,
    'retainer_owner_id': c_uint64,
    'artisan_id': c_uint64,
    'price_per_uint': c_uint,
    'total_tax': c_uint,
    'total_item_count': c_uint,
    'item_id': c_uint,
    'last_review_before': c_ushort,
    'container': c_ushort,
    'slot': c_uint,
    'durability': c_ushort,
    'spiritbond': c_ushort,
    'materias': c_ushort * 5,
    'unk1': c_ushort,
    'unk2': c_uint,
    '_retainer_name': c_ubyte * 32,
    '_player_name': c_ubyte * 32,
    'is_hq': c_bool,
    'materia_count': c_ubyte,
    'is_mannequin': c_bool,
    'retainer_city_id': c_ubyte,
    'stain_id': c_ushort,
    'unk3': c_ushort,
    'unk4': c_uint,
}, extra_properties=['retainer_name', 'player_name'])):
    @property
    def retainer_name(self):
        return bytes(self._retainer_name).decode('utf-8').rstrip("\x00")

    @property
    def player_name(self):
        return bytes(self._player_name).decode('utf-8').rstrip("\x00")

    @cached_property
    def item(self):
        if self.item_id:
            return item_sheet[self.item_id]


ServerMarketBoardItemList = OffsetStruct({
    'items': MarketBoardItemEntry * 10,
    'list_index_end': c_ubyte,
    'list_index_start': c_ubyte,
    'request_id': c_ushort,
    'unk1': c_uint,
}, 1528)

_logger = Logger("XivNetwork/ProcessMarketBoardItemList")
size = sizeof(ServerMarketBoardItemList)
item_sheet = realm.game_data.get_sheet('Item')


class ServerMarketBoardItemListEvent(RecvNetworkEventBase):
    id = "network/recv_market_board_item_list"
    name = "network recv market board item list"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.item_id = self.raw_msg.items[0].item_id
        self.item_count = 0
        for item in self.raw_msg.items:
            if item.item_id:
                self.item_count += 1
            else:
                break

    @cached_property
    def item(self):
        if self.item_id:
            return item_sheet[self.item_id]

    def text(self):
        return f"{self.item['Name']} x{self.item_count} request:{self.raw_msg.request_id}({self.raw_msg.list_index_start} - {self.raw_msg.list_index_end})"


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerMarketBoardItemListEvent(msg_time, header, ServerMarketBoardItemList.from_buffer(raw_msg))
