from ctypes import sizeof

from FFxivPythonTrigger.Logger import Logger
from ..Structs import SendNetworkEventBase, ClientEventAction

_logger = Logger("XivNetwork/ProcessClientEventAction")
size = sizeof(ClientEventAction)


class ClientEventActionEvent(SendNetworkEventBase):
    id = "network/send_event_action"
    name = "network send event action"

    def text(self):
        return f"event action {self.raw_msg.category}-{self.raw_msg.event_id}"


def get_event(msg_time, raw_msg):
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return ClientEventActionEvent(msg_time, ClientEventAction.from_buffer(raw_msg))
