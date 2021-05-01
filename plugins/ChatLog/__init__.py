from .ChatLog import ChatLog, Player
from FFxivPythonTrigger import EventBase, PluginBase, api, process_event
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_pattern, read_memory, read_ubytes
from FFxivPythonTrigger.AddressManager import AddressManager
from ctypes import *
from datetime import datetime
from traceback import format_exc

sig = "48 89 ? ? ? 48 89 ? ? ? 48 89 ? ? ? 57 41 ? 41 ? 48 83 EC ? 48 8B ? ? 48 8B ? 48 2B ? ? 4C 8B"


class ChatLogTable(OffsetStruct({
    'count': (c_ulong, 5 * 4),
    'check_update': (c_ulonglong, 5 * 8),
    'lengths': (POINTER(c_uint), 9 * 8) ,
    'data': (POINTER(c_ubyte), (12 * 8))
})):
    def get_raw(self, idx: int):
        if idx < 0:
            idx = self.count + idx
        if not max(-1, self.count - 1000) < idx < self.count:
            raise IndexError('list index %s out of range' % idx)
        idx %= 1000
        start = self.lengths[idx - 1] if idx > 0 else 0
        return bytes(self.data[start:self.lengths[idx]])

    def get(self, idx: int):
        return ChatLog(self.get_raw(idx))


class ChatLogEvent(EventBase):
    id = "log_event"
    name = "log event"

    def __init__(self, chat_log: ChatLog):
        self.time = datetime.fromtimestamp(chat_log.time)
        self.channel_id = chat_log.channel_id
        self.player = self.player_server = None
        for msg in chat_log.grouped_sender:
            if isinstance(msg, Player):
                self.player = msg.playerName
                self.player_server = msg.serverId
        self.message = chat_log.text
        self.chat_log = chat_log

    def __str__(self):
        return "{}\t{}\t{}\t{}".format(self.time, self.channel_id, self.player or 'n/a', self.message)

    def get_dict(self):
        return {
            't': self.chat_log.time,
            'c': self.channel_id,
            's': self.player,
            'ss': self.player_server,
            'm': self.message
        }


class LogHook(Hook):
    restype = c_int64
    argtypes = [c_int64, c_int64, c_int]

    def __init__(self, func_address: int, addr_recall: callable):
        super().__init__(func_address)
        self.addr_recall = addr_recall

    def hook_function(self, a1, buffer, size):
        try:
            self.addr_recall(a1 - 72)
            process_event(ChatLogEvent(ChatLog(read_ubytes(buffer,size))))
        except Exception:
            _logger.error(format_exc())
            # self.disable()
        return self.original(a1, buffer, size)


class _ApiClass(object):
    chat_log: ChatLogTable = None


class ChatLogPlugin(PluginBase):
    name = "chat log"

    def __init__(self):
        global _logger
        super(ChatLogPlugin, self).__init__()
        _logger = self.logger
        _am = AddressManager(self.storage.data.setdefault('addr', dict()), self.logger)
        addr = _am.get("hook addr", scan_pattern, sig)
        self.storage.save()
        self.hook = LogHook(addr, self.check_addr)
        self.api_class = _ApiClass()
        self.register_api('ChatLog', self.api_class)

    def check_addr(self, addr):
        if self.api_class.chat_log is None:
            self.api_class.chat_log = read_memory(ChatLogTable, addr)

    def _start(self):
        self.hook.enable()

    def _onunload(self):
        self.hook.uninstall()
