from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


@xivrow
class GCScripShopCategory(XivRow):

    @property
    def grand_company(self) -> 'GrandCompany':
        from .grand_company import GrandCompany
        return self.as_T(GrandCompany)

    @property
    def tier(self) -> int:
        return self.as_int32('Tier')

    @property
    def sub_category(self) -> int:
        return self.as_int32('SubCategory')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GCScripShopCategory, self).__init__(sheet, source_row)
