from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .. import text


@xivrow
class PlaceName(XivRow):
    @property
    def name(self) -> text.XivString:
        return self.as_string('Name')

    @property
    def name_without_article(self) -> text.XivString:
        return self.as_string('Name{NoArticle}')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(PlaceName, self).__init__(sheet, source_row)

    def __str__(self):
        return self.name
