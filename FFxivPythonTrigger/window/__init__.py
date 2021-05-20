import ctypes.wintypes
import os

_pid = os.getpid()
_p_hwnds = []


def _filter_func(hwnd, param):
    rtn_value = ctypes.wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(rtn_value))
    if rtn_value.value == _pid:
        str_buffer = (ctypes.c_char * 512)()
        ctypes.windll.user32.GetClassNameA(hwnd, str_buffer, 512)
        if str_buffer.value == b'FFXIVGAME':
            _p_hwnds.append(hwnd)


_c_filter_func = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(_filter_func)
ctypes.windll.user32.EnumWindows(_c_filter_func, 0)
CURRENT_HWND = _p_hwnds[0] if _p_hwnds else None
