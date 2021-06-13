from datetime import datetime
from typing import Optional
from ..Structs import SendNetworkEventBase


class SendPingEvent(SendNetworkEventBase):
    id = "network/send_ping"
    name = "network send ping event"

    def text(self):
        return "ping send"


def get_event(msg_time, raw_msg):
    return SendPingEvent(raw_msg, msg_time)
