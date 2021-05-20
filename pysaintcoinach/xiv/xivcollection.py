from typing import Dict, TypeVar, overload, Type, cast

from ..ex.relational.excollection import RelationalExCollection
from ..ex.relational.sheet import IRelationalSheet
from ..pack import PackCollection
from .sheet import XivSheet, XivRow, XivSheet2, XivSubRow, IXivSheet, IXivRow, IXivSubRow
from ..util import ConcurrentDictionary


T_IXivRow = TypeVar('T_IXivRow', bound=IXivRow)
T_IXivSubRow = TypeVar('T_IXivSubRow', bound=IXivSubRow)


class XivCollection(RelationalExCollection):

    @property
    def enpcs(self) -> 'ENpcCollection':
        from .collections import ENpcCollection
        if self.__enpcs is None:
            self.__enpcs = ENpcCollection(self)
        return self.__enpcs

    @property
    def shops(self) -> 'ShopCollection':
        from .collections import ShopCollection
        if self.__shops is None:
            self.__shops = ShopCollection(self)
        return self.__shops

    def __init__(self, pack_collection: PackCollection):
        super(XivCollection, self).__init__(pack_collection)
        # NOTE: Our port doesn't actually make use of `sheet_name_to_type_map` because we use the decorator
        # instead. Runtime reflection is a bit different in Python.
        self.__sheet_name_to_type_map = ConcurrentDictionary()  # type: ConcurrentDictionary[str, type]
        self.__enpcs = None
        self.__shops = None

    @overload
    def get_sheet(self, t_cls: Type[T_IXivRow]) -> IXivSheet[T_IXivRow]:
        pass

    @overload
    def get_sheet(self, t_cls: Type[T_IXivRow], id: int) -> IXivSheet[T_IXivRow]:
        pass

    @overload
    def get_sheet(self, id: int) -> IXivSheet:
        pass

    @overload
    def get_sheet(self, t_cls: Type[T_IXivRow], name: str) -> IXivSheet[T_IXivRow]:
        pass

    @overload
    def get_sheet(self, name: str) -> IXivSheet[XivRow]:
        pass

    def get_sheet(self, *args):
        def _get_sheet_by_name(name):
            return super(XivCollection, self).get_sheet(name)

        def _get_sheet_by_id(id):
            return super(XivCollection, self).get_sheet(id)

        if len(args) == 1:
            if isinstance(args[0], str):
                return _get_sheet_by_name(args[0])
            elif isinstance(args[0], int):
                return _get_sheet_by_id(args[0])
            else:
                t = args[0]
                name = t.__name__
                return self.get_sheet(t, name)
        else:
            t = args[0]
            if isinstance(args[1], str):
                return cast(t, _get_sheet_by_name(args[1]))
            else:
                return cast(t, _get_sheet_by_id(args[1]))

    @overload
    def get_sheet2(self, t_cls: Type[T_IXivSubRow]) -> XivSheet2[T_IXivSubRow]:
        pass

    @overload
    def get_sheet2(self, t_cls: Type[T_IXivSubRow], name: str) -> XivSheet2[T_IXivSubRow]:
        pass

    @overload
    def get_sheet2(self, name: str) -> XivSheet2[XivSubRow]:
        pass

    def get_sheet2(self, *args) -> XivSheet2[XivSubRow]:
        if len(args) == 1:
            if isinstance(args[0], str):
                return cast(XivSheet2[XivSubRow],
                            super(XivCollection, self).get_sheet(args[0]))
            else:
                t = args[0]
                name = t.__name__
                return self.get_sheet2(t, name)
        else:
            t = args[0]
            return cast(XivSheet2[t],
                        super(XivCollection, self).get_sheet(args[1]))

    def _create_sheet(self, header):
        base_sheet = super(XivCollection, self)._create_sheet(header)
        xiv_sheet = self._create_xiv_sheet(base_sheet)
        if xiv_sheet is not None:
            return xiv_sheet
        if header.variant == 2:
            return XivSheet2[XivSubRow](XivSubRow, self, base_sheet)
        return XivSheet[XivRow](XivRow, self, base_sheet)

    def _create_xiv_sheet(self, source_sheet: IRelationalSheet):
        match = self.__get_xiv_row_type(source_sheet.name)
        if match is None:
            return None

        if source_sheet.header.variant == 2:
            return XivSheet2[match](match, self, source_sheet)
        return XivSheet[match](match, self, source_sheet)

    @staticmethod
    def __get_xiv_row_type(sheet_name: str):
        from . import REGISTERED_ROW_CLASSES
        return REGISTERED_ROW_CLASSES.get(sheet_name, None)
