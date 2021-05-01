from typing import List, Iterable
from ..ex.relational import IRelationalRow
from . import xivrow, XivSubRow, IXivSheet
from .interfaces import IShopListing, IShopListingItem, IShop
from .shop_listing_item import ShopListingItem


@xivrow
class GilShopItem(XivSubRow, IShopListing, IShopListingItem):

    GIL_ITEM_KEY = 1

    @property
    def item(self) -> 'Item':
        from .item import Item
        return self.as_T(Item)

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        from .item import Item
        super(GilShopItem, self).__init__(sheet, source_row)
        self.__cost = ShopListingItem(self,
                                      self.sheet.collection.get_sheet(Item)[self.GIL_ITEM_KEY],
                                      self.item.ask,
                                      False,
                                      0)
        self.__shops = None

    def __str__(self):
        return "{0}".format(self.item)

    def __build_shops(self) -> 'List[GilShop]':
        from .gil_shop import GilShop
        s_sheet = self.sheet.collection.get_sheet(GilShop)
        return list(filter(lambda shop: self in shop._items, s_sheet))

    @property
    def rewards(self) -> 'Iterable[IShopListingItem]':
        yield self

    @property
    def costs(self) -> 'Iterable[IShopListingItem]':
        yield self.__cost

    @property
    def shops(self) -> 'Iterable[IShop]':
        if self.__shops is None:
            self.__shops = self.__build_shops()
        return self.__shops

    @property
    def count(self) -> int:
        return 1

    @property
    def is_hq(self) -> bool:
        return False

    @property
    def collectability_rating(self) -> int:
        return 0

    @property
    def shop_item(self) -> 'IShopListing':
        return self
