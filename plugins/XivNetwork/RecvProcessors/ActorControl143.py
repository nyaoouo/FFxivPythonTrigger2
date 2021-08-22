from ctypes import *
from datetime import datetime
from typing import Optional

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from ..Structs import RecvNetworkEventBase


class InitialCommenceEvent(RecvNetworkEventBase):
    id = "network/actor_control/director_update/initial_commence"
    name = "network initial commence event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.content = raw_msg.param1
        self.time = raw_msg.param3

    def text(self):
        return f"{self.content}({self.time}s)"


class RecommenceEvent(InitialCommenceEvent):
    id = "network/actor_control/director_update/recommence"
    name = "network recommence event"


class LockoutTimeAdjustEvent(InitialCommenceEvent):
    id = "network/actor_control/director_update/lockout_time_adjust"
    name = "network lock out time adjust event"


class ChargeBossLBEvent(RecvNetworkEventBase):
    id = "network/actor_control/director_update/charge_boss_lb"
    name = "network charge_boss_lb event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.content = raw_msg.param1
        self.value1 = raw_msg.param3
        self.value2 = raw_msg.param4

    def text(self):
        return f"{self.content}({self.value1}/{self.value2})"


class MusicChangeEvent(RecvNetworkEventBase):
    id = "network/actor_control/director_update/music_change"
    name = "network music change event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.content = raw_msg.param1
        self.value1 = raw_msg.param3

    def text(self):
        return f"{self.content}({self.value1})"


class FadeOutEvent(RecvNetworkEventBase):
    id = "network/actor_control/director_update/fade_out"
    name = "network fade out event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.content = raw_msg.param1

    def text(self):
        return f"{self.content}"


class FadeInEvent(FadeOutEvent):
    id = "network/actor_control/director_update/fade_in"
    name = "network fade in event"


class BarrierUpEvent(FadeOutEvent):
    id = "network/actor_control/director_update/barrier_up"
    name = "network barrier up event"


class VictoryEvent(RecvNetworkEventBase):
    id = "network/actor_control/director_update/victory"
    name = "network victory event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.zone = raw_msg.param1

    def text(self):
        return f"{self.zone}"


DirectorUpdateCategory = {
    0x40000001: InitialCommenceEvent,
    0x40000006: RecommenceEvent,
    0x80000004: LockoutTimeAdjustEvent,
    0x8000000C: ChargeBossLBEvent,
    0x80000001: MusicChangeEvent,
    0x40000005: FadeOutEvent,
    0x40000010: FadeInEvent,
    0x40000012: BarrierUpEvent,
    0x40000003: VictoryEvent,
}


class LimitBreakEvent(RecvNetworkEventBase):
    id = "network/actor_control/limit_break"
    name = "network limit break event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)
        self.param = raw_msg.param1 & 255

    def text(self):
        return f"{self.param}/10000*3"


class UnknownActorControlEvent(RecvNetworkEventBase):
    id = "network/actor_control/unknown_actor_control_143"
    name = "network unknown actor control 143 event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)

    def text(self):
        return f"unknown actor control category: {self.raw_msg.category} | {hex(self.raw_msg.param1)} | {hex(self.raw_msg.param2)} " \
               f"| {hex(self.raw_msg.param3)} | {hex(self.raw_msg.param4)} | {hex(self.raw_msg.param5)} | {hex(self.raw_msg.param6)}"


class UnknownDirectorUpdateEvent(RecvNetworkEventBase):
    id = "network/actor_control/unknown_director_update"
    name = "network unknown director update event"

    def __init__(self, msg_time, header, raw_msg):
        super().__init__(msg_time, header, raw_msg)

    def text(self):
        return f"unknown director update category: {self.raw_msg.param2} | {hex(self.raw_msg.param1)} | {hex(self.raw_msg.param3)} |" \
               f" {hex(self.raw_msg.param4)} | {hex(self.raw_msg.param5)} | {hex(self.raw_msg.param6)}"


ServerActorControl143 = OffsetStruct({
    'category': c_ushort,
    'padding0': c_ushort,
    'param1': c_uint,
    'param2': c_uint,
    'param3': c_uint,
    'param4': c_uint,
    'param5': c_uint,
    'param6': c_uint,
    'padding1': c_uint,
})
size = sizeof(ServerActorControl143)
_logger = Logger("XivNetwork/ProcessActorControl143")
_unknown_category = set()
_unknown_director_update = set()
_logger.debug("size: %d" % size)


def get_event(msg_time: datetime, header, raw_msg: bytearray) -> Optional[RecvNetworkEventBase]:
    if len(raw_msg) < size:
        _logger.warning("message is too short to parse:[%s]" % raw_msg.hex())
    else:
        msg = ServerActorControl143.from_buffer(raw_msg)
        if msg.category == 109:
            evt = DirectorUpdateCategory[msg.param2] if msg.param2 in DirectorUpdateCategory else UnknownDirectorUpdateEvent
        elif msg.category == 505:
            evt = LimitBreakEvent
        else:
            evt = UnknownActorControlEvent
        return evt(msg_time, header, msg)

# class ServerActorControlCategory:
#     HoT_DoT = 23
#     CancelAbility = 15
#     Death = 6
#     TargetIcon = 34
#     Tether = 35
#     GainEffect = 20
#     LoseEffect = 21
#     UpdateEffect = 22
#     Targetable = 54
#     DirectorUpdate = 109
#     SetTargetSign = 502
#     LimitBreak = 505
#     JobChange = 5
#     EffectRemove = 21
