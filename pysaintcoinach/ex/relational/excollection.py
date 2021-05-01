from typing import overload, cast, TypeVar, Type
from ..excollection import ExCollection
from .datasheet import RelationalDataSheet
from .definition import RelationDefinition
from . import IRelationalRow, IRelationalSheet
from .header import RelationalHeader
from .multisheet import RelationalMultiSheet, RelationalMultiRow


T = TypeVar('T')


class RelationalExCollection(ExCollection):
    @property
    def definition(self) -> RelationDefinition: return self.__definition

    @definition.setter
    def definition(self, value): self.__definition = value

    def __init__(self, pack_collection):
        super(RelationalExCollection, self).__init__(pack_collection)
        self.__definition = RelationDefinition()

    def _create_header(self, name, file):
        return RelationalHeader(self, name, file)

    def _create_sheet(self, header):
        from .. import variant1 as Variant1
        from .. import variant2 as Variant2
        rel_header = header  # type: RelationalHeader
        if rel_header.variant == 2:
            return self.__create_sheet(Variant2.RelationalDataRow, rel_header)
        return self.__create_sheet(Variant1.RelationalDataRow, rel_header)

    def __create_sheet(self, t, header):
        if header.available_languages_count >= 1:
            return RelationalMultiSheet[RelationalMultiRow, t](RelationalMultiRow,
                                                               t, self, header)
        return RelationalDataSheet[t](t, self, header, header.available_languages[0])

    @overload
    def get_sheet(self, t_cls: Type[T], id: int) -> IRelationalSheet[T]:
        pass

    @overload
    def get_sheet(self, id: int) -> IRelationalSheet:
        pass

    @overload
    def get_sheet(self, t_cls: Type[T], name: str) -> IRelationalSheet[T]:
        pass

    @overload
    def get_sheet(self, name: str) -> IRelationalSheet:
        pass

    def get_sheet(self, *args) -> IRelationalSheet:
        if isinstance(args[0], type):
            return cast(IRelationalSheet[T],
                        super(RelationalExCollection, self).get_sheet(args[1]))

        return cast(IRelationalSheet,
                    super(RelationalExCollection, self).get_sheet(args[0]))

    def find_reference(self, key: int) -> IRelationalRow:
        for sheet_def in filter(lambda d: d.is_generic_reference_target,
                                self.definition.sheet_definitions):
            sheet = self.get_sheet(sheet_def.name)
            if not any(filter(lambda r: key in r, sheet.header.data_file_ranges)):
                continue

            if key not in sheet:
                continue

            return sheet[key]

        return None
