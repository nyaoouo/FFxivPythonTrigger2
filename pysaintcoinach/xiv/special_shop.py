from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .interfaces import IShop, IItemSource, IShopListing, IShopListingItem

from typing import Iterable


class SpecialShopListing(IShopListing):

    @property
    def special_shop(self) -> 'SpecialShop':
        return self.__special_shop

    # @property
    # def quest(self):
    #     return self.__quest

    def __init__(self, shop: 'SpecialShop', index: int):
        from .item import Item
        from .shop_listing_item import ShopListingItem
        self.__special_shop = shop

        REWARD_COUNT = 2
        rewards = []
        for i in range(REWARD_COUNT):
            item = shop.as_T(Item, 'Item{Receive}', index, i)
            if item.key == 0:
                continue

            count = shop.as_int32('Count{Receive}', index, i)
            if count == 0:
                continue

            hq = shop.as_boolean('HQ{Receive}', index, i)

            rewards.append(ShopListingItem(self, item, count, hq, 0))
        self.__rewards = rewards
        # self.__quest = shop.as_T(XivRow, 'Quest{Item}', index)

        COST_COUNT = 3
        costs = []
        for i in range(COST_COUNT):
            item = shop.as_T(Item, 'Item{Cost}', index, i)
            if item.key == 0:
                continue

            count = shop.as_int32('Count{Cost}', index, i)
            if count == 0:
                continue

            hq = shop.as_boolean('HQ{Cost}', index, i)
            collectability_rating = shop.as_int16('CollectabilityRating{Cost}', index, i)

            costs.append(ShopListingItem(self, item, count, hq, collectability_rating))
        self.__costs = costs

    @property
    def rewards(self) -> 'Iterable[IShopListingItem]':
        return self.__rewards

    @property
    def costs(self) -> 'Iterable[IShopListingItem]':
        return self.__costs

    @property
    def shops(self) -> 'Iterable[IShop]':
        yield self.special_shop


@xivrow
class SpecialShop(XivRow, IShop, IItemSource):

    @property
    def _items(self) -> 'Iterable[SpecialShopListing]':
        if self.__shop_items is None:
            self.__shop_items = self.__build_shop_items()
        return self.__shop_items

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(SpecialShop, self).__init__(sheet, source_row)
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
        return self.name

    def __build_enpcs(self):
        return self.sheet.collection.enpcs.find_with_data(self.key)

    def __build_shop_items(self):
        COUNT = 60

        items = []
        for i in range(COUNT):
            item = SpecialShopListing(self, i)
            if any(item.rewards):
                items.append(item)

        return items

    @property
    def items(self) -> 'Iterable[Item]':
        from itertools import chain
        if self.__item_source_items is None:
            self.__item_source_items = [r.item for r in chain.from_iterable([i.rewards for i in self._items])]
        return self.__item_source_items
