from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


@xivrow
class GatheringSubCategory(XivRow):

    @property
    def item(self) -> "Item":
        from .item import Item
        return self.as_T(Item)

    @property
    def folklore_book_name(self) -> str:
        return str(self.as_string('FolkloreBook'))

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GatheringSubCategory, self).__init__(sheet, source_row)
