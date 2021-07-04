from ctypes import sizeof

from FFxivPythonTrigger.Logger import Logger
from ..Structs import RecvNetworkEventBase, ServerEventPlay,header_size

_logger = Logger("XivNetwork/ProcessServerEventPlay")
size = sizeof(ServerEventPlay)


class ServerEventPlayEvent(RecvNetworkEventBase):
    id = "network/recv_event_play"
    name = "network recv event play"

    def text(self):
        return f"event play {self.raw_msg.category}-{self.raw_msg.event_id} (target:{hex(self.raw_msg.target_id)})"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < header_size+size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerEventPlayEvent(msg_time, ServerEventPlay.from_buffer(raw_msg[header_size:]))
