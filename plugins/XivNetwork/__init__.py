import time
from ctypes import *
from traceback import format_exc

from FFxivPythonTrigger.memory.res import kernel32
from FFxivPythonTrigger import PluginBase, process_event, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_pattern

from .FindAddr2 import find_recv2, find_send2
from .BundleDecoder import BundleDecoder, extract_single, pack_single
from .Structs import ServerMessageHeader, RecvNetworkEventBase, SendNetworkEventBase, FFXIVBundleHeader
from .RecvProcessors import processors as recv_processors
from .SendProcessors import processors as send_processors

WS_DLL_MODE = True


class RecvRawEvent(RecvNetworkEventBase):
    name = "network recv event"

    def __init__(self, raw_msg, msg_time, header):
        super().__init__(raw_msg, msg_time)
        self.header = header


class SendRawEvent(RecvNetworkEventBase):
    name = "network send event"

    def __init__(self, raw_msg, msg_time, header):
        super().__init__(raw_msg, msg_time)
        self.header = header


recv_events_classes = dict()
send_events_classes = dict()


class WebActionHook(Hook):
    socket = None
    argtypes = [c_int64, POINTER(c_ubyte), c_int]
    restype = c_int


class WsDllHook(Hook):
    socket = None
    argtypes = [c_int64, POINTER(c_ubyte), c_int, c_int]
    restype = c_int


_unknown_opcode = set()

send_sig = "48 83 EC ? 48 8B 49 ? 45 33 C9 FF 15 ? ? ? ? 85 C0"
recv_sig = "48 83 EC ? 48 8B 49 ? 45 33 C9 FF 15 ? ? ? ? 83 F8 ?"
sig2 = "40 53 48 83 EC ? 48 8B D9 48 8B 49 ? 48 83 F9 ? 74 ? 45 33 C9 FF 15 ? ? ? ?"

header_size = sizeof(ServerMessageHeader)

msg_header_keys = {
    'login_user_id': None,
    'unk1': None,
    'unk2': None,
    'unk3': None,
    'unk4': None,
}


class XivNetwork(PluginBase):
    name = "XivNetwork"

    def __init__(self):
        super().__init__()

        self.send_decoder = BundleDecoder(self.process_send_msg)
        self.recv_decoder = BundleDecoder(self.process_recv_msg)

        class SendHook(WebActionHook):
            def hook_function(_self, socket, buffer, size):
                _self.socket = socket
                return _self.send(self.makeup_data(bytearray(buffer[:size])))

            def send(_self, data: bytearray,process = True):
                # self.logger('*', data.hex())
                size = len(data)
                new_data = (c_ubyte * size).from_buffer(data)
                success_size = _self.original(_self.socket, new_data, size)
                if success_size and process:
                    self.send_decoder.store_data(bytearray(new_data[:success_size]).copy())
                return success_size

        class RecvHook(WebActionHook):
            def hook_function(_self, socket, buffer, size):
                _self.socket = socket
                success_size = _self.original(socket, buffer, size)
                if success_size:
                    self.recv_decoder.store_data(bytearray(buffer[:success_size]).copy())
                return success_size

        am = AddressManager(self.storage.data, self.logger)
        self.recv_hook1 = RecvHook(am.get('recv', scan_pattern, recv_sig))
        self.recv_hook2 = RecvHook(am.get('recv2', find_recv2, sig2))
        self.send_hook1 = SendHook(am.get('send', scan_pattern, send_sig))
        self.send_hook2 = SendHook(am.get('send2', find_send2, sig2))
        self.storage.save()

        self.makeups = dict()
        self.register_api('XivNetwork', type('obj', (object,), {
            'register_makeup': self.register_makeup,
            'unregister_makeup': self.unregister_makeup,
            'send_messages': self.send_messages,
        }))

    def register_makeup(self, opcode: int, call: callable):
        if opcode not in self.makeups:
            self.makeups[opcode] = set()
        self.makeups[opcode].add(call)

    def unregister_makeup(self, opcode: int, call: callable):
        try:
            self.makeups[opcode].remove(call)
        except KeyError:
            pass

    def makeup_data(self, data: bytearray) -> bytearray:
        try:
            temp = extract_single(data)
            if temp is None: return data
            data_header, messages = temp
            new_messages = []
            for msg in messages:
                if len(msg) >= header_size:
                    msg_header = ServerMessageHeader.from_buffer(msg)
                    if msg_header.msg_type in self.makeups:
                        for call in self.makeups[msg_header.msg_type]:
                            try:
                                msg_header2, msg2 = call(msg_header, msg[header_size:])
                                if msg_header2 is None:
                                    msg = None
                                    break
                                msg = bytearray(msg_header2) + msg2
                            except Exception:
                                self.logger.error("error in makeup data:\n", format_exc())
                if msg is not None:
                    new_messages.append(msg)
            new_data = pack_single(data_header, new_messages)
            return data if new_data is None else new_data
        except Exception:
            self.logger.error("error in makeup data:\n", format_exc())
            return data

    def process_recv_msg(self, msg_time, msg):
        if len(msg) < header_size: return
        header = ServerMessageHeader.from_buffer(msg)
        if header.msg_type not in recv_events_classes:
            recv_events_classes[header.msg_type] = type(
                f"NetworkRecv{header.msg_type}RawEvent",
                (RecvRawEvent,),
                {'id': f'network/recv_{header.msg_type}'}
            )
        process_event(recv_events_classes[header.msg_type](msg[header_size:], msg_time, header))
        event = recv_processors[header.msg_type](msg_time, msg) if header.msg_type in recv_processors else None
        if event is not None: process_event(event)

    def process_send_msg(self, msg_time, msg):
        if len(msg) < header_size: return
        header = ServerMessageHeader.from_buffer(msg)
        for key in msg_header_keys.keys():
            msg_header_keys[key] = getattr(header, key)
        if header.msg_type not in send_events_classes:
            send_events_classes[header.msg_type] = type(
                f"NetworkSend{header.msg_type}RawEvent",
                (SendRawEvent,),
                {'id': f'network/send_{header.msg_type}'}
            )
        process_event(send_events_classes[header.msg_type](msg[header_size:], msg_time, header))
        event = send_processors[header.msg_type](msg_time, msg) if header.msg_type in send_processors else None
        if event is not None: process_event(event)

    def send_messages(self, messages: list[tuple[int, bytearray]],process = True):
        me = api.XivMemory.actor_table.get_me()
        me_id = me.id if me is not None else 0
        self.send_hook1.send(pack_single(None, [
            bytearray(ServerMessageHeader(
                msg_length=len(msg) + header_size,
                actor_id=me_id,
                msg_type=opcode,
                sec=int(time.time()),
                **msg_header_keys,
            )) + msg for opcode, msg in messages
        ]),process)

    def _start(self):
        self.send_hook1.enable()
        self.send_hook2.enable()
        self.recv_hook1.enable()
        self.recv_hook2.enable()
        self.create_mission(self.recv_decoder.process, limit_sec=-1)
        self.create_mission(self.send_decoder.process, limit_sec=-1)

    def _onunload(self):
        self.send_hook1.uninstall()
        self.send_hook2.uninstall()
        self.recv_hook1.uninstall()
        self.recv_hook2.uninstall()
        self.send_decoder.stop_process()
        self.recv_decoder.stop_process()
