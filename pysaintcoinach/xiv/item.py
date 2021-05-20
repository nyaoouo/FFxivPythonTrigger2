from itertools import filterfalse, chain
from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


def flatten(listOfLists):
    """Flatten one level of nesting"""
    return chain.from_iterable(listOfLists)


def unique_everseen(iterable, key=None):
    """
    List unique elements, preserving order. Remember all elements ever seen.
    """
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element


class ItemBase(XivRow):
    @property
    def name(self):
        return self.get_raw('Name')

    @property
    def description(self):
        return self.get_raw('Description')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(ItemBase, self).__init__(sheet, source_row)


@xivrow
class Item(ItemBase):

    @property
    def is_collectable(self):
        return self.as_boolean('IsCollectable')

    @property
    def bid(self):
        return self.get_raw('Price{Low}')

    @property
    def ask(self):
        return self.get_raw('Price{Mid}')

    @property
    def recipes_as_material(self):
        if self.__recipes_as_material is None:
            self.__recipes_as_material = self.__build_recipes_as_material()
        return self.__recipes_as_material

    @property
    def as_shop_payment(self):
        if self.__as_shop_payment is None:
            self.__as_shop_payment = self.__build_as_shop_payment()
        return self.__as_shop_payment

    @property
    def rarity(self) -> int:
        """
        Gets the rarity of the current item.
        :return: The rarity of the current item.

        1: Common (White)
        2: Uncommon (Green)
        3: Rare (Blue)
        4: Relic (Purple)
        7: Aetherial (Pink)
        """
        return self.as_int32('Rarity')

    @property
    def is_aetherial_reducible(self) -> bool:
        return self.as_int32('AetherialReduce') > 0

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(Item, self).__init__(sheet, source_row)
        self.__recipes_as_material = None
        self.__as_shop_payment = None

    def __build_recipes_as_material(self):
        raise NotImplementedError

    def __build_as_shop_payment(self):
        if self.key == 1:
            return []  # XXX: DO NOT BUILD THIS FOR GIL, THAT WOULD BE BAD!

        shops = self.sheet.collection.shops

        checked_items = []
        shop_item_costs = []
        for item in flatten(
                map(lambda shop: filterfalse(
                        lambda _: _ in checked_items,
                        shop.shop_listings),
                    shops)):
            shop_item_costs.extend(filter(
                lambda _: _.item == self,
                item.costs))
            checked_items.append(item)
        return list(unique_everseen(shop_item_costs))
