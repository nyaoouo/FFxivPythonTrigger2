from re import compile
from . import memory
from .res import structure

allowed_protections = [
    structure.MEMORY_PROTECTION.PAGE_EXECUTE_READ,
    structure.MEMORY_PROTECTION.PAGE_EXECUTE_READWRITE,
    structure.MEMORY_PROTECTION.PAGE_READWRITE,
    structure.MEMORY_PROTECTION.PAGE_READONLY,
]


def _brute_scan(compile_pattern):
    for base, size in memory.get_memory_region_to_scan():
        match = compile_pattern.search(memory.read_ubytes(base, size))
        if match:
            return base + match.span()[0]


def brute_scan(regex_pattern):
    return _brute_scan(compile(regex_pattern))


def _scan_pattern_page(address, compile_pattern):
    mbi = memory.virtual_query(address)
    if mbi is None: raise Exception("virtual query failed")
    next_region = mbi.BaseAddress + mbi.RegionSize

    if mbi.state != structure.MEMORY_STATE.MEM_COMMIT or mbi.protect not in allowed_protections:
        return next_region, None

    match = compile_pattern.search(memory.read_ubytes(address, mbi.RegionSize))

    return next_region, (address + match.span()[0] if match else None)


def scan_pattern_page(address, regex_pattern):
    return _scan_pattern_page(address, compile(regex_pattern))


def scan_pattern_module(module, regex_pattern):
    base_address = module.lpBaseOfDll
    max_address = module.lpBaseOfDll + module.SizeOfImage
    page_address = base_address

    found = None
    compile_pattern = compile(regex_pattern)
    while page_address < max_address:
        next_page, found = _scan_pattern_page(page_address, compile_pattern)
        if found:
            break
        page_address = next_page

    return found


def scan_patterns_module(module, regex_pattern):
    base_address = module.lpBaseOfDll
    max_address = module.lpBaseOfDll + module.SizeOfImage
    page_address = base_address

    compile_pattern = compile(regex_pattern)
    while page_address < max_address:
        next_page, found = _scan_pattern_page(page_address, compile_pattern)
        if found is not None: yield found
        page_address = next_page if found is None else found + 1


def scan_static_address_module(module, regex_pattern, cmd_len: int, ptr_idx: int = None):
    ptr_idx = ptr_idx or cmd_len - 4
    temp = scan_pattern_module(module, regex_pattern)
    if temp is None: return None
    return memory.read_long(temp + ptr_idx) + temp + cmd_len
