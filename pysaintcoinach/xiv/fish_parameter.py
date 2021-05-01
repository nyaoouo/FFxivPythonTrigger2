from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .. import text


@xivrow
class FishParameter(XivRow):

    @property
    def text(self) -> text.XivString:
        return self.as_string('Text')

    @property
    def item(self) -> 'Item':
        from .item import Item
        return self.as_T(Item, 'Item')

    @property
    def is_in_log(self) -> bool:
        return self.as_boolean('IsInLog')

    @property
    def time_restricted(self) -> bool:
        return self.as_boolean('TimeRestricted')

    @property
    def weather_restricted(self) -> bool:
        return self.as_boolean('WeatherRestricted')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(FishParameter, self).__init__(sheet, source_row)

    def __str__(self):
        return str(self.item)
