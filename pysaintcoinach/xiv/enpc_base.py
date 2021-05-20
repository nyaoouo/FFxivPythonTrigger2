from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


@xivrow
class ENpcBase(XivRow):

    DATA_COUNT = 32

    # TODO: Port properties found in the SaintCoinach class.

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(ENpcBase, self).__init__(sheet, source_row)

    def get_data(self, index: int) -> IRelationalRow:
        return self.as_T(IRelationalRow, 'ENpcData', index)

    def get_raw_data(self, index: int) -> int:
        ful_col = self.build_column_name('ENpcData', index)
        raw = self.get_raw(ful_col)
        return int(raw)
