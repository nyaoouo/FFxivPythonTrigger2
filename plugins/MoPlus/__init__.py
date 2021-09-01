import os
from traceback import format_exc

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.AddressManager import AddressManager
from ctypes import *

from FFxivPythonTrigger.memory import read_memory, scan_address, scan_pattern

# get_matrix_singleton_type = CFUNCTYPE(c_int64)
#
# screen_to_world_native_type = CFUNCTYPE(c_bool, c_void_p, c_void_p, c_float, c_void_p, c_void_p)
#
# get_matrix_singleton = lambda: 0
# screen_to_world_native = lambda camPos, clipPos, rayDistance, worldPos, unk1: False

mo_entity_sig = "E8 ? ? ? ? 48 8B ? ? ? 48 8B ? ? ? 4C 8B ? ? ? 41 83 FC"


class MoPlus(PluginBase):
    name = "MoPlus"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/MoPlus'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super().__init__()

        class MoEntityHook(self.PluginHook):
            argtypes = [c_int64, c_int64]

            def hook_function(_self, a1, actor_addr):
                try:
                    self._mo_entity = read_memory(api.XivMemory.struct.Actor.Actor, actor_addr) if actor_addr else None
                except Exception:
                    self.logger.error("error occurred in MoEntityHook:\n" + format_exc())
                _self.original(a1, actor_addr)

        class api_class(object):
            @property
            def entity(_):
                if self._mo_entity is not None:
                    return self._mo_entity
                return api.XivMemory.targets.mouse_over

            @property
            def item(_):
                return None

            @property
            def world_position(_):
                return None

        self._mo_entity = None
        self._mo_item = None

        self.entity_hook = MoEntityHook(
            AddressManager(self.storage.data, self.logger)
                .get("mo_entity_addr", scan_address, mo_entity_sig, cmd_len=5)
            , True)
        self.storage.save()
        # global get_matrix_singleton, screen_to_world_native
        # addr1 = am.get("get_matrix_singleton", scan_address, "E8 ?? ?? ?? ?? 48 8D 4C 24 ?? 48 89 4c 24 ?? 4C 8D 4D ?? 4C 8D 44 24 ??", cmd_len=5)
        # get_matrix_singleton = get_matrix_singleton_type(addr1)
        # self.logger.info(hex(get_matrix_singleton()))
        # addr2 = am.get("screen_to_world_native", scan_pattern, "48 83 EC 48 48 8B 05 ?? ?? ?? ?? 4D 8B D1")
        # screen_to_world_native = screen_to_world_native_type(addr2)

        self._api_class = api_class()
        self.register_api("MoPlus", self._api_class)
