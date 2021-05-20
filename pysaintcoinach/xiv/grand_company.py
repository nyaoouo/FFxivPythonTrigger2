from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .. import text


@xivrow
class GrandCompany(XivRow):

    SEAL_ITEM_OFFSET = 19

    @property
    def name(self) -> text.XivString:
        return self.as_string('Name')

    @property
    def seal_item(self) -> 'Item':
        from .item import Item
        return self.sheet.collection.get_sheet(Item)[self.key + self.SEAL_ITEM_OFFSET]

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GrandCompany, self).__init__(sheet, source_row)

    def __str__(self):
        return str(self.name)
