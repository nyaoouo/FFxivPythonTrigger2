import os
from datetime import datetime
from traceback import format_exc
from ctypes import *

from FFxivPythonTrigger import EventBase, PluginBase, process_event
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from FFxivPythonTrigger.memory import scan_pattern, read_memory
from FFxivPythonTrigger.AddressManager import AddressManager

from .ChatLog import ChatLog

sig = "48 89 ? ? ? 48 89 ? ? ? 48 89 ? ? ? 57 41 ? 41 ? 48 83 EC ? 48 8B ? ? 48 8B ? 48 2B ? ? 4C 8B"


class ChatLogTable(OffsetStruct({
    'count': (c_ulong, 5 * 4),
    'check_update': (c_ulonglong, 5 * 8),
    'lengths': (POINTER(c_uint), 9 * 8),
    'data': (POINTER(c_ubyte), (12 * 8))
})):
    def get_raw(self, idx: int):
        if idx < 0:
            idx = self.count + idx
        if not max(-1, self.count - 1000) < idx < self.count:
            raise IndexError('list index %s out of range' % idx)
        idx %= 1000
        start = self.lengths[idx - 1] if idx > 0 else 0
        return bytearray(self.data[start:self.lengths[idx]])

    def get(self, idx: int):
        return ChatLog.from_buffer(self.get_raw(idx))


class ChatLogEvent(EventBase):
    id = "log_event"
    name = "log event"

    def __init__(self, chat_log: ChatLog):
        self.time = datetime.fromtimestamp(chat_log.timestamp)
        self.channel_id = chat_log.channel_id
        self.player = chat_log.sender_text
        self.message = chat_log.messages_text
        self.chat_log = chat_log

    def text(self):
        return "{}\t{}\t{}\t{}".format(self.time, self.channel_id, self.player or 'n/a', self.message)


class ChatLogPlugin(PluginBase):
    name = "chat log"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/ChatLog2'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super(ChatLogPlugin, self).__init__()
        _am = AddressManager(self.storage.data.setdefault('addr', dict()), self.logger)
        addr = _am.get("hook addr", scan_pattern, sig)
        self.storage.save()

        class LogHook(self.PluginHook):
            restype = c_int64
            argtypes = [c_int64, POINTER(c_ubyte), c_int]

            def hook_function(_self, a1, buffer, size):
                try:
                    if self.api_class.chat_log is None:
                        self.api_class.chat_log = read_memory(ChatLogTable, a1 - 72)
                    process_event(ChatLogEvent(ChatLog.from_buffer(bytearray(buffer[:size]))))
                except Exception:
                    self.logger.error(format_exc())
                return _self.original(a1, buffer, size)

        self.hook = LogHook(addr, True)

        self.api_class = type('', (object,), {'chat_log': None})
        self.register_api('ChatLog', self.api_class)
