from .interfaces import ILocatable, IQuantifiableXivString, IQuantifiable
from .. import text


class ENpc(ILocatable, IQuantifiableXivString):

    @property
    def key(self) -> int:
        return self.__key

    @property
    def collection(self) -> 'ENpcCollection':
        return self.__collection

    @property
    def resident(self) -> 'ENpcResident':
        if self.__resident is None:
            self.__resident = self.collection.resident_sheet[self.key]
        return self.__resident

    @property
    def base(self) -> 'ENpcBase':
        if self.__base is None:
            self.__base = self.collection.base_sheet[self.key]
        return self.__base

    @property
    def singular(self) -> text.XivString:
        return self.resident.singular

    @property
    def plural(self) -> text.XivString:
        from ..ex import Language
        if self.collection.collection.active_language == Language.japanese:
            return self.singular
        return self.resident.plural

    @property
    def title(self) -> text.XivString:
        return self.resident.title

    @property
    def locations(self) -> 'Iterable[ILocation]':
        if self.__locations is None:
            self.__locations = self.__build_locations()
        return self.__locations

    def __init__(self, collection: 'ENpcCollection', key: int):
        self.__key = key
        self.__collection = collection
        self.__base = None
        self.__resident = None
        self.__locations = None

    def __build_levels(self):
        from .level import Level
        return list(filter(lambda _: _.object is not None and _.object.key == self.key,
                           self.collection.collection.get_sheet(Level)))

    def __build_locations(self):
        level_locations = self.__build_levels()

        return level_locations

    @property
    def IQuantifiable(self) -> IQuantifiable:
        class _ENpc_IQuantifiable(IQuantifiable):
            def __init__(self, parent: ENpc):
                self.__parent = parent

            @property
            def singular(self) -> str:
                return str(self.__parent.singular)

            @property
            def plural(self) -> str:
                return str(self.__parent.plural)

        return _ENpc_IQuantifiable(self)

    def __str__(self):
        return str(self.resident.singular)

    def __repr__(self):
        return str(self)
