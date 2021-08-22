from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase

ServerActorGauge = OffsetStruct({
    'buffer': c_ubyte * 16,
}, 0x10)
_logger = Logger("XivNetwork/ProcessActorGauge")
size = sizeof(ServerActorGauge)


class RecvActorGaugeEvent(RecvNetworkEventBase):
    id = "network/actor_gauge"
    name = "network actor gauge event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.buffer = bytearray(raw_msg.buffer)

    def text(self):
        return self.buffer.hex()


def get_event(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
    else:
        return RecvActorGaugeEvent(msg_time, header, ServerActorGauge.from_buffer(raw_msg))
