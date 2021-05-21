from ctypes import *

from FFxivPythonTrigger import PluginBase, process_event
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import BASE_ADDR, scan_pattern
from .BundleDecoder import BundleDecoder
from .RecvProcessors.Structs import ServerMessageHeader, RecvNetworkEventBase
from .RecvProcessors import processors


class UnknownOpcodeEvent(RecvNetworkEventBase):
    id = "network/unknown"
    name = "network unknown event"

    def __init__(self, raw_msg, msg_time, header):
        super().__init__(raw_msg, msg_time)
        self.header = header
        self.opcode = header.msg_type

    def text(self):
        return f"{self.opcode}:{self.raw_msg[sizeof(ServerMessageHeader):].hex()}"


class WebActionHook(Hook):
    argtypes = [c_int64, POINTER(c_ubyte), c_int]
    restype = c_int


_unknown_opcode = set()

send_sig = "48 83 EC ? 48 8B 49 ? 45 33 C9 FF 15 ? ? ? ? 85 C0"
recv_sig = "48 83 EC ? 48 8B 49 ? 45 33 C9 FF 15 ? ? ? ? 83 F8 ?"


class XivNetwork(PluginBase):
    name = "XivNetwork"

    def __init__(self):
        super().__init__()

        self.send_decoder = BundleDecoder()
        self.recv_decoder = BundleDecoder()

        class SendHook(WebActionHook):
            def hook_function(_self, socket, buffer, size):
                success_size = _self.original(socket, buffer, size)
                self.create_mission(self.send_data, bytearray(buffer[:success_size]).copy())
                return success_size

        class RecvHook(WebActionHook):
            def hook_function(_self, socket, buffer, size):
                success_size = _self.original(socket, buffer, size)
                self.create_mission(self.recv_data, bytearray(buffer[:success_size]).copy())
                return success_size

        am = AddressManager(self.storage.data, self.logger)
        self.recv_hook1 = RecvHook(am.get('recv', scan_pattern, recv_sig))
        self.send_hook1 = SendHook(am.get('send', scan_pattern, send_sig))
        self.storage.save()

    def recv_data(self, data):
        if self.recv_decoder.store_data(data):
            while self.recv_decoder.messages:
                self.process_recv_msg(*self.recv_decoder.get_next_message())

    def send_data(self, data):
        if self.send_decoder.store_data(data):
            while self.send_decoder.messages:
                self.process_send_msg(*self.send_decoder.get_next_message())

    def process_recv_msg(self, msg_time, msg):
        if len(msg) < sizeof(ServerMessageHeader): return
        header = ServerMessageHeader.from_buffer(msg)
        # self.logger.debug(msg_time,hex(header.msg_type),msg.hex())
        event = processors[header.msg_type](msg_time, msg) if header.msg_type in processors else None
        if event is None: event = UnknownOpcodeEvent(msg, msg_time, header)
        process_event(event)

    def process_send_msg(self, msg_time, msg):
        pass

    def _start(self):
        self.send_hook1.enable()
        self.recv_hook1.enable()

    def _onunload(self):
        self.send_hook1.uninstall()
        self.recv_hook1.uninstall()
