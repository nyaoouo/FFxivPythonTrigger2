from typing import Iterable
from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet, IXivRow
from .. import text
from .interfaces import IItemSource, ILocation, ILocatable


@xivrow
class FishingSpot(XivRow, IItemSource, ILocatable, ILocation):

    @property
    def gathering_level(self) -> int:
        """
        Gets the level of the current `FishingSpot`.
        """
        return self.as_int32('GatheringLevel')

    @property
    def on_reach_big_fish(self) -> text.XivString:
        """
        Gets the text indicating special conditions have been met.
        """
        return self.as_string('BigFish{OnReach}')

    @property
    def on_end_big_fish(self) -> text.XivString:
        """
        Gets the text indicating special conditions have ended.
        """
        return self.as_string('BigFish{OnEnd}')

    @property
    def fishing_spot_category(self):
        # return self.as_T(int, 'FishingSpotCategory')
        try:
            return self.sheet.collection.get_sheet('FishingRecordType')[self.get_raw('FishingSpotCategory')]
        except:
            return self.as_T(int, 'FishingSpotCategory')

    @property
    def territory_type(self) -> 'TerritoryType':
        from .territory_type import TerritoryType
        return self.as_T(TerritoryType)

    @property
    def x(self) -> int:
        return self.as_int32('X')

    @property
    def z(self) -> int:
        return self.as_int32('Z')

    @property
    def radius(self) -> int:
        return self.as_int32('Radius')

    @property
    def place_name(self) -> 'PlaceName':
        from .placename import PlaceName
        return self.as_T(PlaceName)

    @property
    def items(self):
        if self.__items is None:
            self.__items = self.__build_items()
        return self.__items

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(FishingSpot, self).__init__(sheet, source_row)
        self.__items = None

    def __build_items(self):
        from .item import Item
        COUNT = 10

        items = []
        for i in range(COUNT):
            item = self.as_T(Item, 'Item', i)
            if item.key != 0:
                items.append(item)

        return items

    @property
    def map_x(self) -> float:
        return self.territory_type.map.to_map_coordinate_2d(
            self.x, self.territory_type.map.offset_x)

    @property
    def map_y(self) -> float:
        return self.territory_type.map.to_map_coordinate_2d(
            self.z, self.territory_type.map.offset_y)

    @property
    def locations(self) -> 'Iterable[ILocation]':
        yield self

    def __str__(self):
        return str(self.place_name)
