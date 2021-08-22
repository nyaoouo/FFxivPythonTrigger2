import os
import time
from ctypes import *
from traceback import format_exc
from typing import Callable, Optional, Union

from FFxivPythonTrigger import PluginBase, process_event, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.Utils import Counter, wait_until
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_pattern

from .FindAddr2 import find_recv2, find_send2
from .BundleDecoder import BundleDecoder, extract_single, pack_single
from .Structs import ServerMessageHeader, RecvNetworkEventBase, SendNetworkEventBase, FFXIVBundleHeader
from .RecvProcessors import processors as recv_processors, version_opcodes as recv_version_opcodes
from .SendProcessors import processors as send_processors, version_opcodes as send_version_opcodes


class RecvRawEvent(RecvNetworkEventBase):
    name = "network recv event"


class SendRawEvent(SendNetworkEventBase):
    name = "network send event"


class UnkRecvRawEvent(RecvNetworkEventBase):
    name = "network unknown recv event"
    id = "network/unk_recv"

    def text(self):
        return f"opcode:{self.header.msg_type} len:{len(self.raw_msg)}"


class UnkSendRawEvent(SendNetworkEventBase):
    name = "network unknown send event"
    id = "network/unk_send"

    def text(self):
        return f"opcode:{self.header.msg_type} len:{len(self.raw_msg)}"


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

AcceptOpcode = Union[int, str]


def get_send_opcode(opcode: AcceptOpcode) -> int:
    if isinstance(opcode, int): return opcode
    if opcode in send_version_opcodes: return send_version_opcodes[opcode]
    raise Exception(f"[{opcode}] is not a valid send opcode")


def get_recv_opcode(opcode: AcceptOpcode) -> int:
    if isinstance(opcode, int): return opcode
    if opcode in recv_version_opcodes: return recv_version_opcodes[opcode]
    raise Exception(f"[{opcode}] is not a valid recv opcode")


class XivNetwork(PluginBase):
    name = "XivNetwork"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/XivNetwork'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super().__init__()

        self.send_decoder = BundleDecoder(self.process_send_msg)
        self.recv_decoder = BundleDecoder(self.process_recv_msg)

        class SendHook(WebActionHook):
            def hook_function(_self, socket, buffer, size):
                if size > 64: _self.socket = socket
                # self.logger(hex(socket), hex(cast(buffer, c_void_p).value), size)
                return _self.send(self.makeup_data(bytearray(buffer[:size])), return_size=size, socket=socket)

            def send(_self, data: bytearray, process=True, return_size=None, socket=None):
                # self.logger('*', data.hex())
                if socket is None:
                    if _self.socket is None:
                        raise Exception("No socket record")
                    socket = _self.socket
                size = len(data)
                new_data = (c_ubyte * size).from_buffer(data)
                success_size = _self.original(socket, new_data, size)
                if success_size and process:
                    self.send_decoder.store_data(data[:success_size])
                return success_size if return_size is None else return_size

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

        self.send_counter = Counter()
        self.wait_response = dict()
        self.response_data = dict()

        self.makeups = dict()
        self.register_api('XivNetwork', type('obj', (object,), {
            'register_makeup': self.register_makeup,
            'unregister_makeup': self.unregister_makeup,
            'send_messages': self.send_messages,
        }))

    def register_makeup(self, opcode, call: callable):
        opcode = get_send_opcode(opcode)
        if opcode not in self.makeups:
            self.makeups[opcode] = set()
        self.makeups[opcode].add(call)

    def unregister_makeup(self, opcode, call: callable):
        try:
            self.makeups[get_send_opcode(opcode)].remove(call)
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
            if not new_messages: return bytearray()
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
                {'id': f'network/recv/{header.msg_type}'}
            )
        raw_msg = msg[header_size:]
        process_event(recv_events_classes[header.msg_type](msg_time, header, raw_msg))
        event = (recv_processors[header.msg_type] if header.msg_type in recv_processors else UnkRecvRawEvent)(msg_time, header, raw_msg)
        if header.msg_type in self.wait_response:
            waitings = self.wait_response[header.msg_type]
            for waiting in waitings.copy():
                try:
                    is_response = waiting[1] is None or waiting[1](event)
                except Exception as e:
                    self.logger.error(f"error occurred in response: {waiting[1]},an exception will be returned:\n{format_exc()}")
                    self.response_data[waiting[0]] = e
                    waitings.remove(waiting)
                else:
                    if is_response:
                        self.response_data[waiting[0]] = event
                        waitings.remove(waiting)
                if not waitings:
                    del self.wait_response[header.msg_type]
        process_event(event)

    def process_send_msg(self, msg_time, msg):
        if len(msg) < header_size: return
        header = ServerMessageHeader.from_buffer(msg)
        for key in msg_header_keys.keys():
            msg_header_keys[key] = getattr(header, key)
        if header.msg_type not in send_events_classes:
            send_events_classes[header.msg_type] = type(
                f"NetworkSend{header.msg_type}RawEvent",
                (SendRawEvent,),
                {'id': f'network/send/{header.msg_type}'}
            )
        raw_msg = msg[header_size:]
        process_event(send_events_classes[header.msg_type](msg_time, header, raw_msg))
        event = (send_processors[header.msg_type] if header.msg_type in send_processors else UnkSendRawEvent)(msg_time, header, raw_msg)
        if event is not None: process_event(event)

    def get_response(self, response_id: int):
        if response_id in self.response_data:
            temp = self.response_data[response_id]
            del self.response_data[response_id]
            return temp

    def send_messages(self,
                      messages: list[tuple[AcceptOpcode, bytearray]],
                      process=True,
                      response_opcode: AcceptOpcode = None,
                      response_statement: Callable[[any], bool] = None,
                      response_timeout: float = 5.,
                      response_period: float = 0.01):
        me = api.XivMemory.actor_table.get_me()
        me_id = me.id if me is not None else 0
        _messages = []
        for opcode, msg in messages:
            _messages.append(bytearray(ServerMessageHeader(
                msg_length=len(msg) + header_size,
                actor_id=me_id,
                msg_type=get_send_opcode(opcode),
                sec=int(time.time()),
                **msg_header_keys,
            )) + msg)
        response_id = self.send_counter.get()
        if response_opcode is not None:
            self.wait_response.setdefault(get_recv_opcode(response_opcode), set()).add((response_id, response_statement))
        success_len = self.send_hook1.send(pack_single(None, _messages), process)
        if not success_len:
            raise Exception("Failed to send messages")
        if response_opcode is not None:
            res = wait_until(lambda: self.get_response(response_id), timeout=response_timeout, period=response_period)
            if isinstance(res, Exception):
                raise res
            else:
                return res

    def _start(self):
        self.send_hook1.install()
        self.send_hook2.install()
        self.recv_hook1.install()
        self.recv_hook2.install()
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
