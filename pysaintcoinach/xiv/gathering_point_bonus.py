from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


@xivrow
class GatheringPointBonus(XivRow):

    @property
    def condition(self) -> "GatheringCondition":
        from .gathering_condition import GatheringCondition
        return self.as_T(GatheringCondition, 'Condition')

    @property
    def condition_value(self) -> int:
        return self.as_int32('ConditionValue')

    @property
    def bonus_type(self) -> "GatheringPointBonusType":
        from .gathering_point_bonus_type import GatheringPointBonusType
        return self.as_T(GatheringPointBonusType, 'BonusType')

    @property
    def bonus_value(self) -> int:
        return self.as_int32('BonusValue')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GatheringPointBonus, self).__init__(sheet, source_row)
