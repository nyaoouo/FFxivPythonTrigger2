from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from ..text import XivString


@xivrow
class Weather(XivRow):
    @property
    def name(self) -> XivString: return self.as_string('Name')

    @property
    def description(self) -> XivString: return self.as_string('Description')

    @property
    def icon(self) -> object: return self.as_image('Icon')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(Weather, self).__init__(sheet, source_row)

    def __str__(self):
        return self.name
