from ctypes import *

from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from FFxivPythonTrigger import EventBase


class NetworkEventBase(EventBase):
    id = "network"
    name = "network event"

    def __init__(self, msg_time, header, raw_msg):
        self.raw_msg = raw_msg
        self.header = header
        self.time = msg_time


class SendNetworkEventBase(NetworkEventBase):
    is_send = True


class RecvNetworkEventBase(NetworkEventBase):
    is_send = False


class Waymark:
    A = 0
    B = 1
    C = 2
    D = 3
    One = 4
    Two = 5
    Three = 6
    For = 7


FFXIVBundleHeader = OffsetStruct({
    'magic0': c_uint,
    'magic1': c_uint,
    'magic2': c_uint,
    'magic3': c_uint,
    'epoch': c_ulonglong,
    'length': c_ushort,
    'unk1': c_ushort,
    'unk2': c_ushort,
    'msg_count': c_ushort,
    'encoding': c_ushort,
    'unk3': c_ushort,
    'unk4': c_ushort,
    'unk5': c_ushort,
})

ServerMessageHeader = OffsetStruct({
    'msg_length': c_uint,
    'actor_id': c_uint,
    'login_user_id': c_uint,
    'unk1': c_uint,
    'unk2': c_ushort,
    'msg_type': c_ushort,
    'unk3': c_uint,
    'sec': c_uint,
    'unk4': c_uint,
})

header_size = sizeof(ServerMessageHeader)

ServerPresetWaymark = OffsetStruct({
    'header': ServerMessageHeader,
    'waymark_status': c_uint,
    'x': c_int * 8,
    'z': c_int * 8,
    'y': c_int * 8,
})

ServerWaymark = OffsetStruct({
    'header': ServerMessageHeader,
    'waymark': c_ubyte,
    'status': c_bool,
    'unk0': c_ushort,
    'x': c_int,
    'z': c_int,
    'y': c_int,
})

Vector3 = OffsetStruct({
    'x': c_float,
    'z': c_float,
    'y': c_float,
})
