from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase, header_size


class ServerContainerInfo(OffsetStruct({
    'container_sequence': c_uint,
    'item_count': c_uint,
    'container_id': c_uint,
    'unk': c_uint,
}, 16)): pass


_logger = Logger("XivNetwork/ProcessServerContainerInfo")
size = sizeof(ServerContainerInfo)


class ServerContainerInfoEvent(RecvNetworkEventBase):
    id = "network/recv_container_info"
    name = "network recv container info"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.container_id = self.raw_msg.container_id
        self.count = self.raw_msg.item_count

    def text(self):
        return f"container:{hex(self.container_id)} - item_count:{self.count}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size + header_size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerContainerInfoEvent(msg_time, ServerContainerInfo.from_buffer(raw_msg[header_size:]))
