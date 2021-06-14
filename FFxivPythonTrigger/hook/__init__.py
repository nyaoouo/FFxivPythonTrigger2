from ctypes import *
from typing import Annotated, List
from inspect import stack

from . import EasyHook

RAISE_ERROR = False

class Hook(object):
    """
    a hook class to do local hooks

    ```restype```, ```argtypes``` and ```hook_function``` need to be overridden
    """
    restype: Annotated[any, "the return type of hook function"] = c_void_p
    argtypes: Annotated[List[any], "the argument types of hook function"] = []
    original: Annotated[callable, "the original function"]
    is_enabled: Annotated[bool, "is the hook enabled"]
    is_installed: Annotated[bool, "is the hook installed"]
    IS_WIN_FUNC = False

    def hook_function(self, *args):
        """
        the hooked function
        """
        return self.original(*args)

    def __init__(self, func_address: int):
        """
        create a hook,remember to install and enable it afterwards and uninstall it after use

        :param func_address: address of the function need to be hooked
        """
        self.address = func_address
        self.is_enabled = False
        self.is_installed = False
        self.hook_info = c_void_p()
        self._hook_function = c_void_p()
        self.original = lambda x: x
        self.ACL_entries = (c_ulong * 1)(1)
        caller = stack()[1]
        self.create_at = f"{caller.filename}:{caller.lineno}"

    def install(self) -> None:
        """
        install the hook
        """
        if self.address in hook_manager:
            raise Exception(f"a hook is already installed at [{hex(self.address)}] from [{hook_manager[self.address].create_at}]")

        if self.is_installed:
            if RAISE_ERROR:
                raise Exception("Hook is installed")
            else:
                return
        self.hook_info = EasyHook.HOOK_TRACE_INFO()
        interface = (WINFUNCTYPE if self.IS_WIN_FUNC else CFUNCTYPE)(self.restype, *self.argtypes)

        def _hook_function(*args):
            return self.hook_function(*args)

        self._hook_function = interface(_hook_function)
        if EasyHook.lh_install_hook(self.address, self._hook_function, None, byref(self.hook_info)):
            raise EasyHook.LocalHookError()

        self.is_installed = True
        hook_manager[self.address] = self

        original_func_p = c_void_p()
        if EasyHook.lh_get_bypass_address(byref(self.hook_info), byref(original_func_p)):
            raise EasyHook.LocalHookError()
        self.original = interface(original_func_p.value)

    def uninstall(self) -> None:
        """
        uninstall the hook
        """
        if not self.is_installed:
            if RAISE_ERROR:
                raise Exception("Hook is not installed")
            else:
                return
        EasyHook.lh_uninstall_hook(byref(self.hook_info))
        EasyHook.lh_wait_for_pending_removals()
        self.is_installed = False
        del hook_manager[self.address]

    def enable(self) -> None:
        """
        enable the hook
        """
        if not self.is_installed:
            if RAISE_ERROR:
                raise Exception("Hook is not installed")
            else:
                return
        if EasyHook.lh_set_exclusive_acl(addressof(self.ACL_entries), 1, byref(self.hook_info)):
            raise EasyHook.LocalHookError()
        self.is_enabled = True

    def disable(self) -> None:
        """
        disable the hook
        """
        if not self.is_installed:
            if RAISE_ERROR:
                raise Exception("Hook is not installed")
            else:
                return
        if EasyHook.lh_set_inclusive_acl(addressof(self.ACL_entries), 1, byref(self.hook_info)):
            raise EasyHook.LocalHookError()
        self.is_enabled = False


hook_manager: Annotated[dict[int, Hook], "manage those installed hooks"] = dict()
