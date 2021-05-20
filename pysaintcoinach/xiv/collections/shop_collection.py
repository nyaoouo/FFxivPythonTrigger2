from typing import Iterable, Iterator
from itertools import chain
from ..interfaces import IShop
from .. import XivCollection


class ShopCollection(Iterable[IShop]):

    @property
    def collection(self) -> XivCollection:
        return self.__collection

    def __init__(self, collection: XivCollection):
        self.__collection = collection

    def __iter__(self) -> Iterator[IShop]:
        from ..gil_shop import GilShop
        from ..gc_shop import GCShop
        from ..special_shop import SpecialShop
        from ..fcc_shop import FccShop

        _gil_shop_enumerator = iter(self.__collection.get_sheet(GilShop))
        _gc_shop_enumerator = iter(self.__collection.get_sheet(GCShop))
        _special_shop_enumerator = iter(self.__collection.get_sheet(SpecialShop))
        _fcc_shop_enumerator = iter(self.__collection.get_sheet(FccShop))

        return chain(_gil_shop_enumerator,
                     _gc_shop_enumerator,
                     _special_shop_enumerator,
                     _fcc_shop_enumerator)
