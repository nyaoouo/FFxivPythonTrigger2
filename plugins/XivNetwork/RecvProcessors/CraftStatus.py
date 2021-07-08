from ctypes import sizeof

from FFxivPythonTrigger.Logger import Logger
from ..Structs import RecvNetworkEventBase, ServerCraftStatus, header_size

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
