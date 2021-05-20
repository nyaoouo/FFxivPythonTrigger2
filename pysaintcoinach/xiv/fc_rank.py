from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


@xivrow
class FCRank(XivRow):

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(FCRank, self).__init__(sheet, source_row)
