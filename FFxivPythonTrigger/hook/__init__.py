from . import EasyHook
from ctypes import *
from typing import Annotated, List


class Hook(object):
    """
    a hook class to do local hooks

    ```restype```, ```argtypes``` and ```hook_function``` need to be overridden
    """
    restype: Annotated[any, "the return type of hook function"] = c_void_p
    argtypes: Annotated[List[any], "the argument types of hook function"] = []
    original: Annotated[callable, "the original function"]
    is_enabled: Annotated[bool, "is the hook enabled"]
    IS_WIN_FUNC = False

    def hook_function(self, *args):
        """
        the hooked function
        """
        return self.original(*args)

    def __init__(self, func_address: int):
        """
        create a hook,remember to enable it afterwards and uninstall it after use

        :param func_address: address of the function need to be hooked
        """
        self.address = func_address
        self.is_enabled = False
        self.hook_info = EasyHook.HOOK_TRACE_INFO()
        interface = (WINFUNCTYPE if self.IS_WIN_FUNC else CFUNCTYPE)(self.restype, *self.argtypes)

        def _hook_function(*args):
            return self.hook_function(*args)

        self._hook_function = interface(_hook_function)
        if EasyHook.lh_install_hook(func_address, self._hook_function, None, byref(self.hook_info)):
            raise EasyHook.LocalHookError()

        original_func_p = c_void_p()

        if EasyHook.lh_get_bypass_address(byref(self.hook_info), byref(original_func_p)):
            raise EasyHook.LocalHookError()
        self.original = interface(original_func_p.value)

        self.ACL_entries = (c_ulong * 1)(1)

    def disable(self) -> None:
        """
        disable the hook
        """
        if EasyHook.lh_set_inclusive_acl(addressof(self.ACL_entries), 1, byref(self.hook_info)):
            raise EasyHook.LocalHookError()
        self.is_enabled = False

    def enable(self) -> None:
        """
        enable the hook
        """
        if EasyHook.lh_set_exclusive_acl(addressof(self.ACL_entries), 1, byref(self.hook_info)):
            raise EasyHook.LocalHookError()
        self.is_enabled = True

    def uninstall(self) -> None:
        """
        uninstall the hook, if need, please create a new hook instead of using this
        """
        EasyHook.lh_uninstall_hook(byref(self.hook_info))
        EasyHook.lh_wait_for_pending_removals()
