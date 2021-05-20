from typing import Iterable, Iterator, List, Dict
from ..enpc import ENpc
from ..enpc_base import ENpcBase
from .. import XivCollection


class ENpcCollection(Iterable[ENpc]):

    @property
    def collection(self) -> XivCollection:
        return self.__collection

    @property
    def base_sheet(self) -> 'IXivSheet[ENpcBase]':
        return self.__base_sheet

    @property
    def resident_sheet(self) -> 'IXivSheet[ENpcResident]':
        return self.__resident_sheet

    def __init__(self, xiv_collection: XivCollection):
        from ..enpc_resident import ENpcResident
        self.__inner = {}  # type: Dict[int, ENpc]
        self.__enpc_data_map = None  # type: Dict[int, List[ENpc]]
        self.__collection = xiv_collection
        self.__base_sheet = xiv_collection.get_sheet(ENpcBase)
        self.__resident_sheet = xiv_collection.get_sheet(ENpcResident)

    def __getitem__(self, item: int) -> ENpc:
        return self.get(item)

    def get(self, key: int) -> ENpc:
        if key in self.__inner:
            return self.__inner[key]

        enpc = ENpc(self, key)
        self.__inner[key] = enpc
        return enpc

    def __iter__(self) -> Iterator[ENpc]:
        _base_enumerator = iter(self.base_sheet)
        for o in _base_enumerator:
            yield self.get(o.key)

    def find_with_data(self, value: int) -> Iterable[ENpc]:
        if self.__enpc_data_map is None:
            self.__enpc_data_map = self.__build_data_map()
        return self.__enpc_data_map.get(value) or []

    def __build_data_map(self):
        data_map = {}  # type: Dict[int, List[ENpc]]

        for npc in self:
            for i in range(ENpcBase.DATA_COUNT):
                val = npc.base.get_raw_data(i)
                if val == 0:
                    continue
                l = data_map.get(val)
                if l is None:
                    l = []
                    data_map[val] = l
                l.append(npc)

        return data_map
