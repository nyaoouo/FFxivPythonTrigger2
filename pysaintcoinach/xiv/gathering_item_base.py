from . import XivRow


class GatheringItemBase(XivRow):

    @property
    def item(self) -> "ItemBase":
        from .item import ItemBase
        return self.as_T(ItemBase, 'Item')

    def __str__(self):
        return "{0}".format(self.item)
