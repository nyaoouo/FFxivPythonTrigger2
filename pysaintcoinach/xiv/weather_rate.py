from typing import Iterable, List, Tuple, cast
from datetime import timedelta
from itertools import dropwhile

from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from ..eorzeadatetime import EorzeaDateTime


@xivrow
class WeatherRate(XivRow):
    WEATHER_CHANGE_INTERVAL = timedelta(hours=8)

    @property
    def possible_weathers(self) -> 'Iterable[Weather]':
        return self._possible_weathers

    @property
    def weather_rates(self) -> 'Iterable[Tuple[int, Weather]]':
        return self._weather_rates

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        from .weather import Weather
        super(WeatherRate, self).__init__(sheet, source_row)

        count = 8
        w = []  # type: List[Weather]
        wr = []  # type: List[Tuple[int, Weather]]
        min = 0
        for i in range(count):
            weather = cast(Weather, self[('Weather', i)])
            if weather.key == 0:
                continue
            rate = self.as_int32('Rate', i)

            w += [weather]
            wr += [(min + rate, weather)]

            min += rate

        self._possible_weathers = list(set(w))
        self._weather_rates = wr

    def forecast(self, time: EorzeaDateTime) -> 'Weather':
        def calc_target(time):
            # Generate a number between [0..99] based on time.
            # Convert the Eorzea date/time into Unix Time.
            unix_time = time.get_unix_time()
            # Get the Eorzea hour for weather start.
            bell = int(unix_time / 175)
            # Magic needed for calculations:
            # 16:00 = 0, 00:00 = 8, 08:00 = 16 . . .
            inc = ((bell + 8 - (bell % 8))) % 24
            # Take the Eorzea days since Unix Epoch.
            total_days = int(unix_time / 4200)

            # Make the calculations
            calc_base = (total_days * 100) + inc
            step1 = ((calc_base << 11) & 0xFFFFFFFF) ^ calc_base
            step2 = (step1 >> 8) ^ step1

            return (step2 % 100) & 0xFFFFFFFF

        target = calc_target(time)
        forecasted_weather = next(dropwhile(lambda x: target >= x[0], self._weather_rates), None)
        if forecasted_weather is not None:
            return forecasted_weather[1]
        else:
            return None
