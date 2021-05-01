from typing import Iterable, List
from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .interfaces import IItemSource


@xivrow
class GatheringPointBase(XivRow, IItemSource):

    @property
    def type(self) -> "GatheringType":
        from .gathering_type import GatheringType
        return self.as_T(GatheringType)

    @property
    def gathering_level(self) -> int:
        return self.as_int32('GatheringLevel')

    @property
    def _items(self):
        if self.__items is None:
            self.__items = self.__build_items()
        return self.__items

    @property
    def is_limited(self) -> bool:
        return self.as_boolean('IsLimited')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GatheringPointBase, self).__init__(sheet, source_row)
        self.__items = None
        self.__item_source_items = None  # type: List["Item"]

    def __build_items(self):
        from .gathering_item_base import GatheringItemBase
        COUNT = 8

        items = []
        for i in range(COUNT):
            gib: GatheringItemBase = self[('Item', i)]
            if gib is not None and gib.key != 0 and \
                gib.item is not None and gib.item.key != 0:
                items.append(gib)
            else:
                items.append(None)
        return items

    @property
    def items(self) -> Iterable["Item"]:
        if self.__item_source_items is None:
            self.__item_source_items = list(map(lambda i: i.item,
                                                filter(None, self._items)))
        return self.__item_source_items
