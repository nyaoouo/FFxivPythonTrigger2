import inspect
import os
from . import FFxiv_Version
from .Storage import ModuleStorage, BASE_PATH
from .memory import BASE_ADDR
from .Logger import Logger

_logger = Logger("AddressManager")
_storage = ModuleStorage(BASE_PATH / "Address")
_storage.data = dict()
_storage.save()

force_search = bool(os.environ['address_search'])


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

        frame = inspect.stack()[1]
        _storage.data.setdefault('prev', list()).append([f"{frame.filename}:{frame.lineno}", name, param])

        if self.storage is not None and name in self.storage and not force_search:
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
        _storage.data.setdefault(FFxiv_Version, dict())[name] = offset
        _storage.save()
        self.logger.debug(msg.format(name=name, addr=hex(addr), offset=hex(offset)))
        return addr
