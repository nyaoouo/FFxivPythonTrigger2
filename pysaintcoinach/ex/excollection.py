import io
from typing import TypeVar, Type, overload, cast

from .header import Header
from .datasheet import DataSheet
from .multisheet import MultiRow, MultiSheet
from ..pack import PackCollection
from .language import Language
from .. import ex

T = TypeVar('T')


class ExCollection(object):

    @property
    def pack_collection(self) -> PackCollection:
        return self._pack_collection

    @property
    def active_language(self) -> Language:
        return self._active_language

    @active_language.setter
    def active_language(self, value):
        self._active_language = value

    @property
    def active_language_code(self):
        return self.active_language.get_code()

    @property
    def available_sheets(self):
        return self._available_sheets

    def __init__(self, pack_collection: PackCollection):
        self._sheet_identifiers = {}
        # NOTE: Making _sheets a WeakValueDictionary will greatly slow down
        # relational accesses to a sheet, especially when iterating rows with
        # several related sheets. Unfortunately, Python's GC is a bit too eager
        # to finalize these technically dead references, even though they'll
        # likely be requested again soon (just in a separate scope...)
        self._sheets = dict()
        self._available_sheets = set()
        self._pack_collection = pack_collection

        self.__build_index()

    def __build_index(self):
        ex_root = self.pack_collection.get_file("exd/root.exl")
        if ex_root is None:
            raise FileNotFoundError('exd/root.exl')

        available = []

        with io.BufferedReader(io.BytesIO(ex_root.get_data())) as s:
            s.readline() # EXLT,2

            for line in s:
                line = line.decode()
                if len(line.strip()) == 0:
                    continue

                split = line.split(',')
                if len(split) != 2:
                    continue

                name = split[0]
                id = int(split[1])

                available += [name]
                if id >= 0:
                    self._sheet_identifiers[id] = name

        self._available_sheets = set(available)

    def sheet_exists(self, id_or_name):
        if isinstance(id_or_name, str):
            return id_or_name in self.available_sheets
        else:
            return id_or_name in self._sheet_identifiers

    @overload
    def get_sheet(self, t_cls: Type[T], id: int) -> ex.ISheet[T]:
        pass

    @overload
    def get_sheet(self, id: int) -> ex.ISheet:
        pass

    @overload
    def get_sheet(self, t_cls: Type[T], name: str) -> ex.ISheet[T]:
        pass

    @overload
    def get_sheet(self, name: str) -> ex.ISheet:
        pass

    def get_sheet(self, *args) -> ex.ISheet:
        if isinstance(args[0], type):
            return cast(ex.ISheet[args[0]], self.get_sheet(args[1]))

        if isinstance(args[0], int):
            name = self._sheet_identifiers[args[0]]
        else:
            name = args[0]

        EX_HPATH_FORMAT = "exd/%s.exh"

        sheet = self._sheets.get(name, None)
        if sheet is not None:
            return sheet

        if name not in self.available_sheets:
            raise KeyError("Unknown sheet '%s'" % name)

        exh_path = EX_HPATH_FORMAT % (name)
        exh = self.pack_collection.get_file(exh_path)
        if exh is None:
            raise FileNotFoundError(exh_path)

        header = self._create_header(name, exh)
        sheet = self._create_sheet(header)

        self._sheets[name] = sheet
        return sheet

    def _create_header(self, name, file):
        return Header(self, name, file)

    def _create_sheet(self, header):
        from . import variant1 as Variant1
        from . import variant2 as Variant2
        if header.variant == 1:
            return self.__create_sheet(Variant1.DataRow, header)
        return self.__create_sheet(Variant2.DataRow, header)

    def __create_sheet(self, t, header):
        if header.available_languages_count >= 1:
            return MultiSheet[MultiRow, t](MultiRow, t, self, header)
        return DataSheet[t](t, self, header, header.available_languages[0])
