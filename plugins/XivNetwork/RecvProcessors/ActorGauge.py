from ctypes import sizeof
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger

from ..Structs import ServerActorGauge,RecvNetworkEventBase

_logger = Logger("XivNetwork/ProcessActorGauge")
size = sizeof(ServerActorGauge)


class RecvActorGaugeEvent(RecvNetworkEventBase):
    id = "network/actor_gauge"
    name = "network actor gauge event"

    def __init__(self, raw_msg, msg_time):
        super().__init__(raw_msg, msg_time)
        self.buffer = bytearray(raw_msg.buffer)

    def text(self):
        return self.buffer.hex()


def get_event(msg_time: datetime, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
        return
    return RecvActorGaugeEvent(ServerActorGauge.from_buffer(raw_msg), msg_time)
