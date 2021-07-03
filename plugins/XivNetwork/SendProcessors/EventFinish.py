from ctypes import sizeof

from FFxivPythonTrigger.Logger import Logger
from ..Structs import SendNetworkEventBase, ClientEventFinish

_logger = Logger("XivNetwork/ProcessClientEventFinish")
size = sizeof(ClientEventFinish)


class ClientEventFinishEvent(SendNetworkEventBase):
    id = "network/send_event_finish"
    name = "network send event finish"

    def text(self):
        return f"event finish {self.raw_msg.category}-{self.raw_msg.event_id}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ClientEventFinishEvent(msg_time, ClientEventFinish.from_buffer(raw_msg))
