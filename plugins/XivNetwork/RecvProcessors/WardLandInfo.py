from ctypes import sizeof

from FFxivPythonTrigger.Logger import Logger
from ..Structs import RecvNetworkEventBase, ServerWardLandInfo, header_size

_logger = Logger("XivNetwork/ProcessServerWardLandInfo")
size = sizeof(ServerWardLandInfo)


class ServerWardLandInfoEvent(RecvNetworkEventBase):
    id = "network/recv_ward_land_info"
    name = "network recv ward land info"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)

    def text(self):
        return f"world: {self.raw_msg.world_id} - land: {self.raw_msg.land_id} - ward: {self.raw_msg.ward_id} - territory_type: {self.raw_msg.territory_type} - empty:{len(list(self.raw_msg.houses_without_owner()))}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < header_size + size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerWardLandInfoEvent(msg_time, ServerWardLandInfo.from_buffer(raw_msg[header_size:]))
