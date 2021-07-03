from ctypes import sizeof

from FFxivPythonTrigger.Logger import Logger
from ..Structs import RecvNetworkEventBase, ServerEventFinish

_logger = Logger("XivNetwork/ProcessServerEventFinish")
size = sizeof(ServerEventFinish)


class ServerEventFinishEvent(RecvNetworkEventBase):
    id = "network/recv_event_finish"
    name = "network recv event finish"

    def text(self):
        return f"event finish {self.raw_msg.category}-{self.raw_msg.event_id}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ServerEventFinishEvent(msg_time, ServerEventFinish.from_buffer(raw_msg))
