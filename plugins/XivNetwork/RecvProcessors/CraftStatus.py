from ctypes import *

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ..Structs import RecvNetworkEventBase, header_size


class ServerCraftStatus(OffsetStruct({
    'actor_id': (c_uint, 0),
    'prev_action_id': (c_uint, 0x2c),
    'round': (c_uint, 0x34),
    'current_progress': (c_int, 0x38),
    'add_progress': (c_int, 0x3c),
    'current_quality': (c_int, 0x40),
    'add_quality': (c_int, 0x44),
    'current_durability': (c_int, 0x4c),
    'add_durability': (c_int, 0x50),
    'status_id': (c_ushort, 0x54),
    'prev_action_flag': (c_ushort, 0x5c),
}, 160, ['prev_action_success'])):

    @property
    def prev_action_success(self):
        return bool(self.prev_action_flag & 0x10)


_logger = Logger("XivNetwork/ProcessServerCraftStatus")
size = sizeof(ServerCraftStatus)


class ServerCraftStatusEvent(RecvNetworkEventBase):
    id = "network/recv_craft_status"
    name = "network recv craft status"

    def __init__(self, msg_time, raw_msg):
        super().__init__(msg_time, raw_msg)
        self.round = raw_msg.round
        self.current_progress = raw_msg.current_progress
        self.current_quality = raw_msg.current_quality
        self.current_durability = raw_msg.current_durability
        self.status_id = raw_msg.status_id

    def text(self):
        return f"round:{self.round}({self.current_progress}/{self.current_quality}/{self.current_durability})status:{self.status_id}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < header_size + size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerCraftStatusEvent(msg_time, ServerCraftStatus.from_buffer(raw_msg[header_size:]))
