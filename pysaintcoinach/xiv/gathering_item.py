from ..ex.relational import IRelationalRow
from . import xivrow, IXivSheet
from .gathering_item_base import GatheringItemBase


@xivrow
class GatheringItem(GatheringItemBase):

    @property
    def is_hidden(self) -> bool:
        return self.as_boolean('IsHidden')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GatheringItem, self).__init__(sheet, source_row)
