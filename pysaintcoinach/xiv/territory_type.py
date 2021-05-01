from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet


@xivrow
class TerritoryType(XivRow):
    _weather_groups = None
    _maps_by_index = None

    @property
    def name(self): return self.as_string('Name')

    @property
    def bg(self): return self.as_string('Bg')

    @property
    def map(self):
        from .map import Map
        return self.as_T(Map)

    @property
    def place_name(self):
        from .placename import PlaceName
        return self.as_T(PlaceName, 'PlaceName')

    @property
    def region_place_name(self):
        from .placename import PlaceName
        return self.as_T(PlaceName, 'PlaceName{Region}')

    @property
    def zone_place_name(self):
        from .placename import PlaceName
        return self.as_T(PlaceName, 'PlaceName{Zone}')

    @property
    def weather_rate(self):
        if self._weather_rate is not None:
            return self._weather_rate
        if self._weather_groups is None:
            self._weather_groups = self._build_weather_groups()

        rate_key = self.as_int32('WeatherRate')
        self._weather_rate = self._weather_groups.get(rate_key)
        if self._weather_rate is None:
            self._weather_rate = self.sheet.collection.get_sheet('WeatherRate')[rate_key]
        return self._weather_rate

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(TerritoryType, self).__init__(sheet, source_row)
        self._weather_rate = None
        self._maps_by_index = None

    def get_related_map(self, index: int):
        if self._maps_by_index is None:
            self._maps_by_index = self._build_map_index()

        _map = self._maps_by_index.get(index)
        if _map is not None:
            return _map

        # Fallback to the default map. This may not be accurate.
        return self.map

    def _build_weather_groups(self):
        _map = {}
        for weather_group in self.sheet.collection.get_sheet('WeatherGroup'):
            if weather_group.key != 0:
                continue

            _map[weather_group.parent_row.key] = weather_group['WeatherRate']
        return _map

    def _build_map_index(self):
        _maps = filter(lambda m: m['TerritoryType'] == self.key,
                       self.sheet.collection.get_sheet('Map'))

        _index = {}

        for _map in _maps:
            map_id = str(_map.as_string('Id'))
            if map_id is None or map_id == '':
                continue

            map_index = map_id[map_id.index('/') + 1:]
            converted_index = int(map_index)
            if converted_index in _index:
                continue  # skip it for now

            _index[converted_index] = _map

        return _index
