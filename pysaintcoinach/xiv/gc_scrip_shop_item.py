from ..ex.relational import IRelationalRow
from . import xivrow, XivSubRow, IXivSheet
from .interfaces import IShopListing, IShopListingItem
from .shop_listing_item import ShopListingItem


@xivrow
class GCScripShopItem(XivSubRow, IShopListing, IShopListingItem):

    @property
    def gc_shop(self) -> 'GCShop':
        return self.__gc_shop

    @property
    def cost(self) -> ShopListingItem:
        return self.__cost

    @property
    def gc_scrip_shop_category(self) -> 'GCScripShopCategory':
        return self.__gc_scrip_shop_category

    @property
    def item(self) -> 'Item':
        from .item import Item
        return self.as_T(Item)

    @property
    def required_grand_company_rank(self) -> 'GrandCompanyRank':
        # TODO: Use `GrandCompanyRank` type.
        return self['Required{GrandCompanyRank}']

    @property
    def gc_seals_cost(self) -> int:
        return self.as_int32('Cost{GCSeals}')

    @property
    def sort_key(self) -> int:
        return self.get_raw('SortKey') & 0xFF

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        from .gc_shop import GCShop
        from .gc_scrip_shop_category import GCScripShopCategory
        super(GCScripShopItem, self).__init__(sheet, source_row)
        self.__gc_scrip_shop_category = self.sheet.collection.get_sheet(GCScripShopCategory)[self.parent_key]
        self.__gc_shop = next(filter(lambda _: _.grand_company.key == self.gc_scrip_shop_category.grand_company.key,
                                     self.sheet.collection.get_sheet(GCShop)))

        seal_item = self.gc_shop.grand_company.seal_item
        self.__cost = ShopListingItem(self, seal_item, self.gc_seals_cost, False, 0)

    def __str__(self):
        return str(self.item)

    @property
    def rewards(self) -> 'Iterable[IShopListingItem]':
        yield self

    @property
    def costs(self) -> 'Iterable[IShopListingItem]':
        yield self.cost

    @property
    def shops(self) -> 'Iterable[IShop]':
        yield self.gc_shop

    @property
    def is_hq(self) -> bool:
        return False

    @property
    def shop_item(self) -> 'IShopListing':
        return self

    @property
    def collectability_rating(self) -> int:
        return 0

    @property
    def count(self) -> int:
        return 1
