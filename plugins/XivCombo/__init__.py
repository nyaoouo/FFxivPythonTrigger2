from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger import PluginBase
from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger import api
from ctypes import *
from traceback import format_exc

from FFxivPythonTrigger.memory import scan_pattern
from . import DarkKnight, Machinist, Dancer, Gunbreaker, RedMage, Warrior, Bard

combos = DarkKnight.combos | Machinist.combos | Dancer.combos | Gunbreaker.combos | RedMage.combos | Warrior.combos | Bard.combos

# get_icon_sig = "48 89 ? ? ? 48 89 ? ? ? 48 89 ? ? ? 57 48 83 EC ? 8B DA BE" #cn.5.35
get_icon_sig = "48 89 ? ? ? 48 89 ? ? ? 57 48 83 EC ? 8B DA BE"  # cn.5.40
is_icon_replaceable_sig = "81 F9 ?? ?? ?? ?? 7F 39 81 F9 ?? ?? ?? ??"
_logger: Logger


class OnGetIconHook(Hook):
    restype = c_ulonglong
    argtypes = [c_ubyte, c_uint]

    def __init__(self, func_address: int):
        super().__init__(func_address)
        self.err = 0

    def hook_function(self, a1, action_id):
        if action_id in combos:
            try:
                me = api.XivMemory.actor_table.get_me()
                if me is not None:
                    return self.original(a1, combos[action_id](me))
            except Exception:
                if _logger is not None:
                    _logger.error("error occured:\n" + format_exc())
        return self.original(a1, action_id)


class OnCheckIsIconReplaceableHook(Hook):
    restype = c_ulonglong
    argtypes = [c_uint]

    def hook_function(self, action_id):
        return action_id in combos or self.original(action_id)
        # return 1


class XivCombo(PluginBase):
    name = "xiv combo"

    def __init__(self):
        global _logger
        super().__init__()
        _logger = self.logger
        am = AddressManager(self.storage.data, self.logger)
        get_icon_addr = am.get("get icon", scan_pattern, get_icon_sig)
        is_icon_replaceable_addr = am.get("is icon replaceable", scan_pattern, is_icon_replaceable_sig)
        self.storage.save()
        self.on_get_icon_hook = OnGetIconHook(get_icon_addr)
        self.on_is_icon_replaceable_hook = OnCheckIsIconReplaceableHook(is_icon_replaceable_addr)
        self.on_get_icon_hook.enable()
        self.on_is_icon_replaceable_hook.enable()

    def _onunload(self):
        self.on_get_icon_hook.uninstall()
        self.on_is_icon_replaceable_hook.uninstall()
