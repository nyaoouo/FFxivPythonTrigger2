from ctypes import *

from FFxivPythonTrigger import PluginBase, process_event
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import BASE_ADDR
from .BundleDecoder import BundleDecoder
from .Structs import ServerMessageHeader
from .Processors import processors


class WebActionHook(Hook):
    argtypes = [c_int64, POINTER(c_ubyte), c_int]
    restype = c_int


_unknown_opcode = set()


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

        self.recv_hook1 = RecvHook(BASE_ADDR + 0x11FF5F0)
        self.send_hook1 = SendHook(BASE_ADDR + 0x11FF5C0)

    def recv_data(self, data):
        if self.recv_decoder.store_data(data):
            while self.recv_decoder.messages:
                self.process_msg(*self.recv_decoder.get_next_message(), False)

    def send_data(self, data):
        if self.send_decoder.store_data(data):
            while self.send_decoder.messages:
                self.process_msg(*self.send_decoder.get_next_message(), True)

    def process_msg(self, msg_time, msg, is_send):
        if len(msg) < sizeof(ServerMessageHeader):
            return
        header = ServerMessageHeader.from_buffer(msg)
        # self.logger.debug(msg_time,hex(header.msg_type),msg.hex())
        if is_send:
            return
        if header.msg_type in processors:
            event = processors[header.msg_type](msg_time, msg)
            if event is not None:
                event.is_send = is_send
                process_event(event)
        elif header.msg_type not in _unknown_opcode:
            _unknown_opcode.add(header.msg_type)
            self.logger.debug(f"unknown opcode {hex(header.msg_type)}")

    def _start(self):
        self.send_hook1.enable()
        self.recv_hook1.enable()

    def _onunload(self):
        self.send_hook1.uninstall()
        self.recv_hook1.uninstall()
