from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .interfaces import IShop, ILocatable, IItemSource


@xivrow
class GCShop(XivRow, IShop, ILocatable, IItemSource):

    @property
    def grand_company(self) -> 'GrandCompany':
        from .grand_company import GrandCompany
        return self.as_T(GrandCompany)

    @property
    def _items(self) -> 'Iterable[GCScripShopItem]':
        if self.__items is None:
            self.__items = self.__build_items()
        return self.__items

    @property
    def locations(self) -> 'Iterable[ILocation]':
        from itertools import chain
        return chain.from_iterable(map(lambda _: _.locations, self.enpcs))

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GCShop, self).__init__(sheet, source_row)
        self.__enpcs = None
        self.__items = None
        self.__item_source_items = None

    @property
    def enpcs(self) -> 'Iterable[ENpc]':
        if self.__enpcs is None:
            self.__enpcs = self.__build_enpcs()
        return self.__enpcs

    @property
    def shop_listings(self) -> 'Iterable[IShopListing]':
        return self._items

    @property
    def name(self) -> str:
        return "{0}".format(self.grand_company)

    def __build_enpcs(self):
        return self.sheet.collection.enpcs.find_with_data(self.key)

    def __build_items(self):
        from operator import attrgetter
        from .gc_scrip_shop_category import GCScripShopCategory
        from .gc_scrip_shop_item import GCScripShopItem
        items = []

        gc_shop_category_keys = \
            set(map(attrgetter('key'),
                    filter(lambda c: c.grand_company.key == self.grand_company.key,
                           self.sheet.collection.get_sheet(GCScripShopCategory))))

        for gc_item in self.sheet.collection.get_sheet2(GCScripShopItem):
            if gc_item.item.key != 0 and gc_item.parent_key in gc_shop_category_keys:
                items.append(gc_item)

        return items

    @property
    def items(self) -> 'Iterable[Item]':
        if self.__item_source_items is None:
            self.__item_source_items = list(map(lambda i: i.item, self._items))
        return self.__item_source_items

    def __str__(self):
        return str(self.grand_company)
