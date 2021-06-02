from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger import FFxiv_Version

from .Opcodes import opcodes

_logger = Logger("XivNetwork/SendProcessors")

_processors = {}

processors = dict()
_opcodes = opcodes.setdefault(FFxiv_Version,dict())
for k, p in _processors.items():
    if k not in _opcodes: continue
    _logger.debug(f"load opcode of [{k}]({hex(_opcodes[k])})")
    processors[_opcodes[k]] = p
