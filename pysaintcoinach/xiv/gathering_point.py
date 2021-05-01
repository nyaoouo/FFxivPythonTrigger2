from typing import List
from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


@xivrow
class GatheringPoint(XivRow):

    @property
    def base(self) -> "GatheringPointBase":
        from .gathering_point_base import GatheringPointBase
        return self.as_T(GatheringPointBase)

    @property
    def territory_type(self) -> "TerritoryType":
        from .territory_type import TerritoryType
        return self.as_T(TerritoryType)

    @property
    def place_name(self) -> "PlaceName":
        from .placename import PlaceName
        return self.as_T(PlaceName)

    @property
    def gathering_point_bonus(self) -> List["GatheringPointBonus"]:
        if self.__bonuses is None:
            self.__bonuses = self.__build_gathering_point_bonus()
        return self.__bonuses

    @property
    def gathering_sub_category(self) -> "GatheringSubCategory":
        from .gathering_sub_category import GatheringSubCategory
        return self.as_T(GatheringSubCategory)

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GatheringPoint, self).__init__(sheet, source_row)
        self.__bonuses = None

    def __build_gathering_point_bonus(self):
        from .gathering_point_bonus import GatheringPointBonus
        COUNT = 2

        bonuses = []
        for i in range(COUNT):
            bonus = self.as_T(GatheringPointBonus, None, i)
            if bonus.key != 0:
                bonuses.append(bonus)

        return bonuses
