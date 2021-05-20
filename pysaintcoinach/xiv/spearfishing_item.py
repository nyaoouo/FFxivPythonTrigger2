from ..ex.relational import IRelationalRow
from . import xivrow, IXivSheet
from .gathering_item_base import GatheringItemBase


@xivrow
class SpearfishingItem(GatheringItemBase):

    @property
    def item_level(self) -> int:
        return self.as_int32('ItemLevel')

    @property
    def is_visible(self) -> bool:
        return self.as_boolean('IsVisible')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(SpearfishingItem, self).__init__(sheet, source_row)
