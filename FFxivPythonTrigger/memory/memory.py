from ctypes import *
from .res import structure, kernel32
from .process import CURRENT_PROCESS_HANDLER
from .exception import WinAPIError


def allocate_memory(size, handle=CURRENT_PROCESS_HANDLER, allocation_type=None, protection_type=None):
    if not allocation_type:
        allocation_type = structure.MEMORY_STATE.MEM_COMMIT.value
    if not protection_type:
        protection_type = structure.MEMORY_PROTECTION.PAGE_EXECUTE_READWRITE.value
    windll.kernel32.SetLastError(0)
    address = kernel32.VirtualAllocEx(handle, None, size, allocation_type, protection_type)
    return address


def virtual_query(address):
    mbi = structure.MEMORY_BASIC_INFORMATION()
    if kernel32.VirtualQueryEx(CURRENT_PROCESS_HANDLER, address, byref(mbi), sizeof(mbi)) == sizeof(structure.MEMORY_BASIC_INFORMATION):
        return mbi


def get_memory_region_to_scan():
    pos = 0
    mbi = structure.MEMORY_BASIC_INFORMATION()
    size = sizeof(structure.MEMORY_BASIC_INFORMATION)
    while kernel32.VirtualQueryEx(CURRENT_PROCESS_HANDLER, pos, byref(mbi), sizeof(mbi)) == size:
        if mbi.Protect & 256 != 256 and mbi.Protect & 4 == 4:
            yield mbi.BaseAddress, mbi.RegionSize
        next_addr = mbi.BaseAddress + mbi.RegionSize
        if pos >= next_addr: break
        pos = next_addr


def read_memory(data_type, address: int):
    return cast(address, POINTER(data_type))[0]


def read_ubytes(address: int, size: int) -> bytearray:
    return bytearray(read_memory(c_ubyte * size, address))


def read_sbyte(address: int) -> int:
    return read_memory(c_byte, address)


def read_ubyte(address: int) -> int:
    return read_memory(c_ubyte, address)


def read_short(address: int) -> int:
    return read_memory(c_short, address)


def read_ushort(address: int) -> int:
    return read_memory(c_ushort, address)


def read_int(address: int) -> int:
    return read_memory(c_int, address)


def read_uint(address: int) -> int:
    return read_memory(c_uint, address)


def read_long(address: int) -> int:
    return read_memory(c_long, address)


def read_ulong(address: int) -> int:
    return read_memory(c_ulong, address)


def read_longlong(address: int) -> int:
    return read_memory(c_longlong, address)


def read_ulonglong(address: int) -> int:
    return read_memory(c_ulonglong, address)


def read_float(address: int) -> float:
    return read_memory(c_float, address)


def read_double(address: int) -> float:
    return read_memory(c_double, address)


def read_string(address: int, size: int = 100, coding: str = 'utf-8') -> str:
    return read_memory(c_char * size, address).value.decode(coding, errors='ignore')


def write_bytes(address: int, data, size=None, handler=CURRENT_PROCESS_HANDLER) -> None:
    windll.kernel32.SetLastError(0)
    dst = cast(address, c_char_p)
    res = kernel32.WriteProcessMemory(handler, dst, data, size or len(data), None)
    error_code = windll.kernel32.GetLastError()
    if error_code:
        windll.kernel32.SetLastError(0)
        raise WinAPIError(error_code)
    return res


def write_memory(data_type, address: int, data, handler=CURRENT_PROCESS_HANDLER):
    raw = cast((data_type * 1)(data), POINTER(c_ubyte))
    write_bytes(address, raw, sizeof(data_type), handler)


def write_string(address: int, data: str, coding: str = 'utf-8', size: int = None) -> None:
    raw = bytearray(data.encode(coding))
    raw.append(0)
    if size is not None and len(raw) > size:
        raw = raw[:size]
    return write_ubytes(address, raw)


def write_ubytes(address: int, data: bytearray) -> None:
    d_type = c_ubyte * len(data)
    write_memory(d_type, address, d_type.from_buffer(data))


def write_sbyte(address: int, data: int) -> None:
    write_memory(c_byte, address, data)


def write_ubyte(address: int, data: int) -> None:
    write_memory(c_ubyte, address, data)


def write_short(address: int, data: int) -> None:
    write_memory(c_short, address, data)


def write_ushort(address: int, data: int) -> None:
    write_memory(c_ushort, address, data)


def write_int(address: int, data: int) -> None:
    write_memory(c_int, address, data)


def write_uint(address: int, data: int) -> None:
    write_memory(c_uint, address, data)


def write_long(address: int, data: int) -> None:
    write_memory(c_long, address, data)


def write_ulong(address: int, data: int) -> None:
    write_memory(c_ulong, address, data)


def write_longlong(address: int, data: int) -> None:
    write_memory(c_longlong, address, data)


def write_ulonglong(address: int, data: int) -> None:
    write_memory(c_ulonglong, address, data)


def write_float(address: int, data: float) -> None:
    write_memory(c_float, address, data)


def write_double(address: int, data: float) -> None:
    write_memory(c_double, address, data)
