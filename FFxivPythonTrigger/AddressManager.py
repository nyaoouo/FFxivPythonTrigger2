from . import FFxiv_Version
from .memory import BASE_ADDR
from .Logger import Logger

_logger = Logger("AddressManager")


class AddressSearchError(Exception):
    def __init__(self, name):
        msg = "searching address of [%s] is failed" % name
        _logger.error(msg)
        super(AddressSearchError, self).__init__(msg)


class AddressManager(object):
    def __init__(self, storage=None, logger=None):
        self.storage = storage.setdefault(FFxiv_Version, dict()) if storage is not None else None
        self.logger = logger or _logger

    def get(self, name, call, param, add=0, **kwargs):
        if self.storage is not None and name in self.storage:
            offset = self.storage[name]
            addr = offset + BASE_ADDR
            msg = "address load [{addr}] [+{offset}] \"{name}\""
        else:
            addr = call(param, **kwargs)
            if addr is None:
                raise AddressSearchError(name)
            addr += add
            offset = addr - BASE_ADDR
            if self.storage is not None:
                self.storage[name] = offset
            msg = "address found [{addr}] [+{offset}] \"{name}\""
        self.logger.debug(msg.format(name=name, addr=hex(addr), offset=hex(offset)))
        return addr
