from ctypes import *
from ctypes.util import find_library
from pathlib import Path

c_ulong_p = POINTER(c_ulong)
c_void_pp = POINTER(c_void_p)

res_path = str(Path(__file__).parent / 'res' / 'EasyHook64.dll')
lib_path = find_library(res_path)
clib = cdll.LoadLibrary(lib_path)


class HOOK_TRACE_INFO(Structure):
    _fields_ = [("Link", c_void_p)]


TRACED_HOOK_HANDLE = POINTER(HOOK_TRACE_INFO)

lh_install_hook = clib.LhInstallHook
lh_install_hook.restype = c_ulong
lh_install_hook.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p]

lh_uninstall_hook = clib.LhUninstallHook
lh_uninstall_hook.restype = c_ulong
lh_uninstall_hook.argtypes = [c_void_p]

lh_uninstall_all_hooks = clib.LhUninstallAllHooks
lh_uninstall_all_hooks.restype = c_ulong

rtl_get_last_error = clib.RtlGetLastError
rtl_get_last_error.restype = c_ulong

rtl_get_last_error_string = clib.RtlGetLastErrorString
rtl_get_last_error_string.restype = c_wchar_p

lh_set_inclusive_acl = clib.LhSetInclusiveACL
lh_set_inclusive_acl.restype = c_ulong
lh_set_inclusive_acl.argtypes = [c_void_p, c_ulong, c_void_p]

lh_set_exclusive_acl = clib.LhSetExclusiveACL
lh_set_exclusive_acl.restype = c_ulong
lh_set_exclusive_acl.argtypes = [c_void_p, c_ulong, c_void_p]

lh_get_bypass_address = clib.LhGetHookBypassAddress
lh_get_bypass_address.restype = c_ulong
lh_get_bypass_address.argtypes = [c_void_p, c_void_pp]

lh_wait_for_pending_removals = clib.LhWaitForPendingRemovals


class LocalHookError(Exception):
    def __init__(self):
        self.code = rtl_get_last_error()
        self.err_msg = rtl_get_last_error_string()
        super(LocalHookError, self).__init__("code[%s]:%s" % (hex(self.code), self.err_msg))


if __name__ == '__main__':
    from ctypes.wintypes import *

    t_dll = CDLL('User32.dll')
    t_dll.MessageBoxW.argtypes = [HWND, LPCWSTR, LPCWSTR, UINT]
    test = lambda: t_dll.MessageBoxW(None, 'hi content!', 'hi title!', 0)
    test()

    interface = CFUNCTYPE(c_int, HWND, LPCWSTR, LPCWSTR, UINT)


    def fake_function(handle, title, message, flag):
        print(title, message)
        return t_original(handle, "hooked " + title, "hooked " + message, flag)


    hook_f = interface(fake_function)

    t_hook_info = HOOK_TRACE_INFO()
    if lh_install_hook(t_dll.MessageBoxW, hook_f, None, byref(t_hook_info)):
        raise LocalHookError()

    original_func_p = c_void_p()

    if lh_get_bypass_address(byref(t_hook_info), byref(original_func_p)):
        raise LocalHookError()
    t_original = interface(original_func_p.value)
    t_original(None, 'o content!', 'o title!', 0)

    ACLEntries = (c_ulong * 1)(0)
    if lh_set_inclusive_acl(addressof(ACLEntries), 1, byref(t_hook_info)):
        raise LocalHookError()
    print('inclusive')
    test()

    if lh_set_exclusive_acl(addressof(ACLEntries), 1, byref(t_hook_info)):
        raise LocalHookError()
    print('exclusive')
    test()

    if lh_set_inclusive_acl(addressof(ACLEntries), 1, byref(t_hook_info)):
        raise LocalHookError()
    print('inclusive')
    test()

    if lh_uninstall_hook(byref(t_hook_info)):
        raise LocalHookError()
    print('uninstalled')
    test()

    if lh_wait_for_pending_removals():
        raise LocalHookError()

    print('end')
