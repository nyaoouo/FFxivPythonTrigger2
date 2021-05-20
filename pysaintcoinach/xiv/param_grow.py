from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet, IXivRow


@xivrow
class ParamGrow(XivRow):

    @property
    def exp_to_next(self) -> int:
        return self.as_int32('ExpToNext')

    @property
    def additional_actions(self) -> int:
        return self.as_int32('AdditionalActions')

    @property
    def mp_modifier(self) -> float:
        return self.as_int32('MpModifier') / 100.0

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(ParamGrow, self).__init__(sheet, source_row)
