from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet, IXivRow
from .interfaces import ILocation


@xivrow
class Level(XivRow, ILocation):
    @property
    def x(self) -> float: return self.as_single('X')

    @property
    def y(self) -> float: return self.as_single('Y')

    @property
    def z(self) -> float: return self.as_single('Z')

    @property
    def map_x(self) -> float: return self.map.to_map_coordinate_3d(self.x, self.map.offset_x)

    @property
    def map_y(self) -> float: return self.map.to_map_coordinate_3d(self.z, self.map.offset_y)

    @property
    def yaw(self) -> float: return self.as_single('Yaw')

    @property
    def radius(self) -> float: return self.as_single('Radius')

    @property
    def type(self) -> int: return self.as_int32('Type')

    @property
    def object(self) -> IXivRow: return self.as_T(IXivRow, 'Object')

    @property
    def map(self) -> 'Map':
        from .map import Map
        return self.as_T(Map)

    @property
    def place_name(self) -> 'PlaceName': return self.map.place_name

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(Level, self).__init__(sheet, source_row)
