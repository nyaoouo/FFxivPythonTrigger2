from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet, IXivRow
from .. import text
from ..imaging import ImageFile
from typing import cast


@xivrow
class ClassJob(XivRow):
    ICON_OFFSET = 62000
    FRAMED_ICON_OFFSET = 62100
    ICON_FORMAT = 'ui/icon/{0:3u}000/{1:6u}.tex'

    @property
    def name(self) -> text.XivString:
        return self.as_string('Name')

    @property
    def abbreviation(self) -> text.XivString:
        return self.as_string('Abbreviation')

    @property
    def class_job_category(self) -> 'ClassJobCategory':
        from .class_job_category import ClassJobCategory
        return self.as_T(ClassJobCategory)

    @property
    def parent_class_job(self) -> 'ClassJob':
        return self.as_T(ClassJob, 'ClassJob{Parent}')

    @property
    def starting_weapon(self) -> 'Item':
        from .item import Item
        return self.as_T(Item, 'Item{StartingWeapon}')

    @property
    def soul_crystal(self) -> 'Item':
        from .item import Item
        return self.as_T(Item, 'Item{SoulCrystal}')

    @property
    def starting_level(self) -> int:
        return self.get_raw('StartingLevel') & 0xFF

    @property
    def icon(self) -> ImageFile:
        nr = ClassJob.ICON_OFFSET + self.key
        path = ClassJob.ICON_FORMAT.format(nr / 1000, nr)
        file = self.sheet.collection.pack_collection.get_file(path)
        if file is not None:
            return cast(ImageFile, file)
        return None

    @property
    def framed_icon(self) -> ImageFile:
        nr = ClassJob.FRAMED_ICON_OFFSET + self.key
        path = ClassJob.ICON_FORMAT.format(nr / 1000, nr)
        file = self.sheet.collection.pack_collection.get_file(path)
        if file is not None:
            return cast(ImageFile, file)
        return None

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(ClassJob, self).__init__(sheet, source_row)

    def __str__(self):
        return self.name
