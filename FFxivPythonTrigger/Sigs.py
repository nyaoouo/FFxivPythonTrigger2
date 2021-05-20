from .memory import scan_address, scan_pattern

frame_inject = {
    'call': scan_pattern,
    'param': "4C 8B DC 53 56 48 81 EC 18 02 00 00 48 8B 05",
}
