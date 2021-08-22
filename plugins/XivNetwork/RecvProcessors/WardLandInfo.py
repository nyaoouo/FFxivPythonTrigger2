from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase


class LandHouseEntry(OffsetStruct({
    'price': c_uint,
    '_flag': c_uint,
    '_owner': c_char * 32
}, extra_properties=['owner', 'is_fc'])):
    @property
    def owner(self):
        return self._owner.decode('utf-8', errors='ignore')

    @property
    def is_fc(self):
        return bool(self._flag & (1 << 4))


class ServerWardLandInfo(OffsetStruct({
    'land_id': c_ushort,
    'ward_id': c_ushort,
    'territory_type': c_ushort,
    'world_id': c_ushort,
    'houses': LandHouseEntry * 60
})):
    def houses_without_owner(self):
        for house in self.houses:
            if not house.owner:
                yield house


_logger = Logger("XivNetwork/ProcessServerWardLandInfo")
size = sizeof(ServerWardLandInfo)


class ServerWardLandInfoEvent(RecvNetworkEventBase):
    id = "network/recv_ward_land_info"
    name = "network recv ward land info"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)

    def text(self):
        return f"world: {self.raw_msg.world_id} - land: {self.raw_msg.land_id} - ward: {self.raw_msg.ward_id} - territory_type: {self.raw_msg.territory_type} - empty:{len(list(self.raw_msg.houses_without_owner()))}"


def get_event(msg_time, header, raw_msg):
    if len(raw_msg) <  size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerWardLandInfoEvent(msg_time, header, ServerWardLandInfo.from_buffer(raw_msg))
