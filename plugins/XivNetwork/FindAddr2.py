from FFxivPythonTrigger.memory import *

module_handle = kernel32.GetModuleHandleW("WS2_32.dll")
recv_addr = kernel32.GetProcAddress(module_handle, b'recv')
send_addr = kernel32.GetProcAddress(module_handle, b'send')


def find_recv2(sig):
    p = ida_sig_to_pattern(sig)
    pl = len(p)
    for a in scan_patterns_base_module(p):
        if read_ulonglong(read_long(a + pl - 4) + pl + a) == recv_addr:
            return a


def find_send2(sig):
    p = ida_sig_to_pattern(sig)
    pl = len(p)
    for a in scan_patterns_base_module(p):
        if read_ulonglong(read_long(a + pl - 4) + pl + a) == send_addr:
            return a
