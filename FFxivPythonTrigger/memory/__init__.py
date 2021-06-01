from . import process, pattern
from .memory import *

BASE_MODULE = process.base_module()
BASE_ADDR = BASE_MODULE.lpBaseOfDll if BASE_MODULE is not None else None
PROCESS_FILENAME = process.get_current_process_filename()
special_chars_map = {i for i in b'()[]{}?*+-|^$\\.&~# \t\n\r\v\f'}


def scan_pattern_base_module(regex_pattern: bytes) -> int:
    return pattern.scan_pattern_module(BASE_MODULE, regex_pattern)


def scan_patterns_base_module(regex_pattern: bytes):
    return pattern.scan_patterns_module(BASE_MODULE, regex_pattern)


def scan_static_address_base_module(regex_pattern: bytes, cmd_len: int, ptr_idx: int = None):
    return pattern.scan_static_address_module(BASE_MODULE, regex_pattern, cmd_len, ptr_idx)


def ida_sig_to_pattern(ida_sig: str):
    ans = []
    for s in ida_sig.split(' '):
        if s and s[0] == '?':
            ans.append(46)
        elif s:
            temp = int(s, 16)
            if temp in special_chars_map:
                ans.append(0x5c)
            ans.append(temp)
    return bytes(ans)


def scan_static_address_by_sig_base_module(ida_sig: str, cmd_len: int, ptr_idx: int = None):
    return scan_static_address_base_module(ida_sig_to_pattern(ida_sig), cmd_len, ptr_idx)


def scan_pattern_by_sig_base_module(ida_sig: str):
    return scan_pattern_base_module(ida_sig_to_pattern(ida_sig))


def scan_patterns_by_sig_base_module(ida_sig: str):
    return scan_patterns_base_module(ida_sig_to_pattern(ida_sig))


def read_pointer_shift(base, *shifts):
    ptr = base
    for shift in shifts:
        ptr = read_ulonglong(ptr) + shift
    return ptr


scan_pattern = scan_pattern_by_sig_base_module
scan_address = scan_static_address_by_sig_base_module
