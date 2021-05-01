from typing import List, Iterable
from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .interfaces import IShop, IShopListing, IShopListingItem


@xivrow
class FccShop(XivRow, IShop):

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
        if self.__shop_listings is None:
            self.__shop_listings = self.__build_shop_listings()
        return self.__shop_listings

    @property
    def items(self) -> 'Iterable[Item]':
        if self.__items is None:
            self.__items = self.__build_items()
        return self.__items

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(FccShop, self).__init__(sheet, source_row)
        self.__enpcs = None
        self.__shop_listings = None
        self.__items = None

    def __build_enpcs(self):
        return self.sheet.collection.enpcs.find_with_data(self.key)

    ITEM_COUNT = 10

    def __build_shop_listings(self):
        from .item import Item
        from .fc_rank import FCRank

        COST_ITEM = 6559  # TODO: This is the company chest; because there's no item for FC credit :(

        cost_item = self.sheet.collection.get_sheet(Item)[COST_ITEM]
        listings = []  # type: List[IShopListing]
        for i in range(self.ITEM_COUNT):
            item = self.as_T(Item, 'Item', i)
            if item is None or item.key == 0:
                continue

            cost = self.as_int32('Cost', i)
            required_rank = self.as_T(FCRank, 'FCRank{Required}', i)

            listings.append(FccShop.Listing(self, item, cost_item, cost, required_rank))
        return listings

    def __build_items(self):
        from .item import Item

        items = []  # type: List[Item]
        for i in range(self.ITEM_COUNT):
            item = self.as_T(Item, 'Item', i)
            if item is not None and item.key != 0:
                items.append(item)
        return items

    class Listing(IShopListing):

        def __init__(self,
                     shop: 'FccShop',
                     reward_item: 'Item',
                     cost_item: 'Item',
                     cost_count: int,
                     required_fc_rank: 'FCRank'):
            from .shop_listing_item import ShopListingItem

            self._shop = shop  # type: IShop
            self._cost = ShopListingItem(self, cost_item, cost_count, False, 0)  # type: IShopListingItem
            self._reward = ShopListingItem(self, reward_item, 1, False, 0)  # type: IShopListingItem

        @property
        def costs(self) -> 'Iterable[IShopListingItem]':
            yield self._cost

        @property
        def rewards(self) -> 'Iterable[IShopListingItem]':
            yield self._reward

        @property
        def shops(self) -> 'Iterable[IShop]':
            yield self._shop

    def __str__(self):
        return str(self.name)
