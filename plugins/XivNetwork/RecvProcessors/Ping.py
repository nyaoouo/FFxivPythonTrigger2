from datetime import datetime
from typing import Optional
from ..Structs import RecvNetworkEventBase


class RecvPingEvent(RecvNetworkEventBase):
    id = "network/recv_ping"
    name = "network recv ping event"

    def text(self):
        return "ping recv"


def get_event(msg_time, raw_msg):
    return RecvPingEvent(msg_time, raw_msg)
