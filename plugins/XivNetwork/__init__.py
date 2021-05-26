from ctypes import *
from traceback import format_exc

from FFxivPythonTrigger import PluginBase, process_event
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_pattern
from .BundleDecoder import BundleDecoder, extract_single, pack_single
from .Structs import ServerMessageHeader, RecvNetworkEventBase, SendNetworkEventBase
from .RecvProcessors import processors as recv_processors
from .SendProcessors import processors as send_processors


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
    argtypes = [c_int64, POINTER(c_ubyte), c_int]
    restype = c_int


_unknown_opcode = set()

send_sig = "48 83 EC ? 48 8B 49 ? 45 33 C9 FF 15 ? ? ? ? 85 C0"
recv_sig = "48 83 EC ? 48 8B 49 ? 45 33 C9 FF 15 ? ? ? ? 83 F8 ?"

header_size = sizeof(ServerMessageHeader)


class XivNetwork(PluginBase):
    name = "XivNetwork"

    def __init__(self):
        super().__init__()

        self.send_decoder = BundleDecoder()
        self.recv_decoder = BundleDecoder()

        class SendHook(WebActionHook):
            def hook_function(_self, socket, buffer, size):
                new_data = self.makeup_data(bytearray(buffer[:size]))
                size = len(new_data)
                new_data = (c_ubyte * size).from_buffer(new_data)
                success_size = _self.original(socket, new_data, size)
                if success_size: self.create_mission(self.send_data, bytearray(new_data[:success_size]).copy())
                return success_size

        class RecvHook(WebActionHook):
            def hook_function(_self, socket, buffer, size):
                success_size = _self.original(socket, buffer, size)
                if success_size: self.create_mission(self.recv_data, bytearray(buffer[:success_size]).copy())
                return success_size

        am = AddressManager(self.storage.data, self.logger)
        self.recv_hook1 = RecvHook(am.get('recv', scan_pattern, recv_sig))
        self.send_hook1 = SendHook(am.get('send', scan_pattern, send_sig))
        self.storage.save()

        self.makeups = dict()
        self.register_api('XivNetwork', type('obj', (object,), {
            'register_makeup': self.register_makeup,
            'unregister_makeup': self.unregister_makeup,
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
                    opcode = ServerMessageHeader.from_buffer(msg).msg_type
                    if opcode in self.makeups:
                        for call in self.makeups[opcode]:
                            try:
                                msg = call(msg)
                            except Exception:
                                self.logger.error("error in makeup data:\n", format_exc())
                new_messages.append(msg)
            new_data = pack_single(data_header, new_messages)
            return data if new_data is None else new_data
        except Exception:
            self.logger.error("error in makeup data:\n", format_exc())
            return data

    def recv_data(self, data):
        if self.recv_decoder.store_data(data):
            while self.recv_decoder.messages:
                self.process_recv_msg(*self.recv_decoder.get_next_message())

    def send_data(self, data):
        if self.send_decoder.store_data(data):
            while self.send_decoder.messages:
                self.process_send_msg(*self.send_decoder.get_next_message())

    def process_recv_msg(self, msg_time, msg):
        if len(msg) < header_size: return
        header = ServerMessageHeader.from_buffer(msg)
        if header.msg_type not in recv_events_classes:
            recv_events_classes[header.msg_type] = type(
                f"NetworkRecv{header.msg_type}RawEvent",
                (RecvRawEvent,),
                {'id': f'network/recv_{header.msg_type}'}
            )
        process_event(recv_events_classes[header.msg_type](msg, msg_time, header))
        event = recv_processors[header.msg_type](msg_time, msg) if header.msg_type in recv_processors else None
        if event is not None: process_event(event)

    def process_send_msg(self, msg_time, msg):
        if len(msg) < header_size: return
        header = ServerMessageHeader.from_buffer(msg)
        # self.logger(header.msg_type,msg[:24].hex())
        if header.msg_type not in send_events_classes:
            send_events_classes[header.msg_type] = type(
                f"NetworkSend{header.msg_type}RawEvent",
                (SendRawEvent,),
                {'id': f'network/send_{header.msg_type}'}
            )
        process_event(send_events_classes[header.msg_type](msg, msg_time, header))
        event = send_processors[header.msg_type](msg_time, msg) if header.msg_type in send_processors else None
        if event is not None: process_event(event)

    def _start(self):
        self.send_hook1.enable()
        self.recv_hook1.enable()

    def _onunload(self):
        self.send_hook1.uninstall()
        self.recv_hook1.uninstall()
