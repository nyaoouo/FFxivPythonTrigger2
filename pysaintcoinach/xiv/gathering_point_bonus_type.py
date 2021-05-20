from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .. import text


@xivrow
class GatheringPointBonusType(XivRow):

    @property
    def text(self) -> text.XivString:
        return self.as_string('Text')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GatheringPointBonusType, self).__init__(sheet, source_row)

    def __str__(self):
        return str(self.text)
