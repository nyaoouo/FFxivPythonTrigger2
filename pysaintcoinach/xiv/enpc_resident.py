from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet
from .. import text
from .interfaces import IQuantifiableXivString, IQuantifiable


@xivrow
class ENpcResident(XivRow, IQuantifiableXivString):

    @property
    def singular(self) -> text.XivString:
        return self.as_string('Singular')

    @property
    def plural(self) -> text.XivString:
        from ..ex import Language
        if self.collection.active_language == Language.japanese:
            return self.singular
        return self.as_string('Plural')

    @property
    def title(self) -> text.XivString:
        return self.as_string('Title')

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(ENpcResident, self).__init__(sheet, source_row)

    def __str__(self):
        return str(self.singular)

    @property
    def IQuantifiable(self) -> IQuantifiable:
        class _ENpcResident_IQuantifiable(IQuantifiable):
            def __init__(self, parent: ENpcResident):
                self.__parent = parent

            @property
            def singular(self) -> str:
                return str(self.__parent.singular)

            @property
            def plural(self) -> str:
                return str(self.__parent.plural)

        return _ENpcResident_IQuantifiable(self)
