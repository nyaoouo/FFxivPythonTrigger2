from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet, IXivRow
from .. import text
from typing import Iterable


@xivrow
class ClassJobCategory(XivRow):

    @property
    def name(self) -> text.XivString:
        return self.as_string('Name')

    @property
    def class_jobs(self) -> 'Iterable[ClassJob]':
        if self.__class_jobs is None:
            self.__class_jobs = self.__build_class_jobs()
        return self.__class_jobs

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(ClassJobCategory, self).__init__(sheet, source_row)
        self.__class_jobs = None

    def __build_class_jobs(self):
        COLUMN_OFFSET = 1

        cjs = []
        cj_sheet = self.sheet.collection.get_sheet('ClassJob')
        for cj in cj_sheet:
            is_valid = self[COLUMN_OFFSET + cj.key]
            if is_valid:
                cjs.append(cj)
        return cjs

    def __str__(self):
        return self.name
