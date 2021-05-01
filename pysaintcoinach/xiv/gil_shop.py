from typing import Iterable
from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .interfaces import IShop, IItemSource


@xivrow
class GilShop(XivRow, IShop, IItemSource):

    @property
    def _items(self) -> 'Iterable[GilShopItem]':
        if self.__shop_items is None:
            self.__shop_items = self.__build_shop_items()
        return self.__shop_items

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GilShop, self).__init__(sheet, source_row)
        self.__enpcs = None
        self.__shop_items = None
        self.__item_source_items = None

    @property
    def name(self) -> str:
        return str(self.as_string('Name'))

    @property
    def enpcs(self) -> 'Iterable[ENpc]':
        if self.__enpcs is None:
            self.__enpcs = self.__build_enpcs()
        return self.__enpcs

    @property
    def shop_listings(self) -> 'Iterable[IShopListing]':
        return self._items

    def __str__(self):
        return str(self.name)

    def __build_enpcs(self):
        return self.sheet.collection.enpcs.find_with_data(self.key)

    def __build_shop_items(self):
        from .gil_shop_item import GilShopItem
        return [r for r in self.sheet.collection.get_sheet2(GilShopItem)
                if r.parent_key == self.key]

    @property
    def items(self) -> 'Iterable[Item]':
        if self.__item_source_items is None:
            self.__item_source_items = list(map(lambda i: i.item, self._items))
        return self.__item_source_items
