from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .. import text
from ..imaging import ImageFile


@xivrow
class GatheringType(XivRow):

    @property
    def name(self) -> text.XivString:
        return self.as_string('Name')

    @property
    def main_icon(self) -> ImageFile:
        return self.as_image('Icon{Main}')

    @property
    def sub_icon(self) -> ImageFile:
        return self.as_image('Icon{Off}')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(GatheringType, self).__init__(sheet, source_row)

    def __str__(self):
        return str(self.name)
