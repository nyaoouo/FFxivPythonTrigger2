from collections.abc import Iterable
from pathlib import Path
from weakref import WeakValueDictionary
import io
import logging
from typing import Iterable as IterableT, Dict, Tuple, IO
from threading import Lock
import threading

from .util import ConcurrentDictionary


logger = logging.getLogger(__name__)


class PackIdentifier(object):
    DEFAULT_EXPANSION = "ffxiv"

    TYPE_TO_KEY_MAP = {"common": 0x00,
                       "bgcommon": 0x01,
                       "bg": 0x02,
                       "cut": 0x03,
                       "chara": 0x04,
                       "shader": 0x05,
                       "ui": 0x06,
                       "sound": 0x07,
                       "vfx": 0x08,
                       #"ui_script": 0x09,
                       "exd": 0x0a,
                       "game_script": 0x0b,
                       "music": 0x0c,
                       "_sqpack_test": 0x12,
                       "_debug": 0x13,}

    KEY_TO_TYPE_MAP = dict([(v, k) for (k, v) in TYPE_TO_KEY_MAP.items()])

    EXPANSION_TO_KEY_MAP = {"ffxiv": 0x00,
                            "ex1": 0x01,
                            "ex2": 0x02,
                            "ex3": 0x03}

    KEY_TO_EXPANSION_MAP = dict([(v, k) for (k, v) in EXPANSION_TO_KEY_MAP.items()])

    @property
    def type(self) -> str: return self._type

    @property
    def type_key(self) -> int: return self._type_key

    @property
    def expansion(self) -> str: return self._expansion

    @property
    def expansion_key(self) -> int: return self._expansion_key

    @property
    def number(self) -> int: return self._number

    def __init__(self, type, expansion, number):
        if isinstance(type, str):
            self._type = type
            self._type_key = self.TYPE_TO_KEY_MAP[type]
        else:
            self._type_key = type
            self._type = self.KEY_TO_TYPE_MAP[type]
        if isinstance(expansion, str):
            self._expansion = expansion
            self._expansion_key = self.EXPANSION_TO_KEY_MAP[expansion]
        else:
            self._expansion_key = expansion
            self._expansion = self.KEY_TO_EXPANSION_MAP[expansion]
        self._number = number

    def __hash__(self):
        return self.type_key << 16 | self.expansion_key << 8 | self.number

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return other.type_key == self.type_key and \
                other.expansion_key == self.expansion_key and \
                other.number == self.number
        return False

    def __repr__(self):
        return "PackId(%s, %s, %u)" % (self.type, self.expansion, self.number)

    @staticmethod
    def get(full_path: str):
        type_sep = full_path.find('/')
        if type_sep <= 0:
            return None
        type = full_path[:type_sep]
        if type not in PackIdentifier.TYPE_TO_KEY_MAP:
            return None

        exp_sep = full_path.find('/', type_sep+1)

        expansion = None
        number = 0
        if exp_sep > type_sep:
            expansion = full_path[type_sep+1:exp_sep]
            number_end = full_path.find('_', exp_sep)
            if number_end - exp_sep == 3:
                try:
                    number = int(full_path[exp_sep+1:number_end], 16)
                except RuntimeError:
                    number = 0

        if expansion is None or expansion not in PackIdentifier.EXPANSION_TO_KEY_MAP:
            expansion = PackIdentifier.DEFAULT_EXPANSION

        return PackIdentifier(type, expansion, number)


class PackCollection(object):
    @property
    def data_directory(self): return self._data_directory

    @property
    def packs(self) -> 'IterableT[Pack]': return self._packs.values()

    def __init__(self, data_directory):
        if isinstance(data_directory, str):
            data_directory = Path(data_directory)
        if isinstance(data_directory, Path):
            if not (data_directory.exists() and data_directory.is_dir()):
                raise FileNotFoundError
        else:
            raise TypeError("data_directory")
        self._data_directory = data_directory
        self._packs = ConcurrentDictionary()  # type: ConcurrentDictionary[PackIdentifier, Pack]

    def file_exists(self, path: str):
        pack = self.get_pack(path)
        return pack is not None and pack.file_exists(path)

    def get_file(self, path: str):
        pack = self.get_pack(path)
        return pack.get_file(path) if pack is not None else None

    def get_pack(self, id_or_path):
        if isinstance(id_or_path, PackIdentifier):
            _id = id_or_path
        else:
            _id = PackIdentifier.get(id_or_path)
        if _id is None:
            return None

        return self._packs.get_or_add(_id, lambda i: Pack(self.data_directory, _id, self))


class Pack(Iterable):
    """
    Class for a SqPack.
    """
    _INDEX_FILE_FORMAT = "{0:02x}{1:02x}{2:02x}.win32.index"
    _INDEX2_FILE_FORMAT = "{0:02x}{1:02x}{2:02x}.win32.index2"
    _DAT_FILE_FORMAT = "{0:02x}{1:02x}{2:02x}.win32.dat{3}"

    @property
    def id(self) -> PackIdentifier: return self._id

    @property
    def collection(self) -> PackCollection: return self._collection

    @property
    def data_directory(self): return self._data_directory

    @property
    def source(self): return self._source

    @property
    def keep_in_memory(self): return self._keep_in_memory

    @keep_in_memory.setter
    def keep_in_memory(self, value):
        if value == self.keep_in_memory:
            return

        if len(self._data_streams) > 0:
            logger.error("Failed to keep pack %r in memory." % self.id)
            return

        self._keep_in_memory = value
        if not value:
            self._buffers.clear()

    def __init__(self,
                 data_directory,
                 id: PackIdentifier,
                 collection: PackCollection = None):
        # Import here to prevent mutual dependency.
        from .indexfile import IndexSource, Index, Index2Source, Index2

        if isinstance(data_directory, str):
            data_directory = Path(data_directory)
        if isinstance(data_directory, Path):
            if not (data_directory.exists() and data_directory.is_dir()):
                raise FileNotFoundError
        else:
            raise TypeError("data_directory")

        self._collection = collection
        self._data_directory = data_directory
        self._id = id
        self._data_streams = {}  # type: Dict[Tuple[int, int], IO]
        self._data_streams_lock = Lock()
        self._keep_in_memory = False
        self._buffers = {}  # type: Dict[int, bytes]

        index_path = data_directory.joinpath(id.expansion, self._INDEX_FILE_FORMAT.format(id.type_key, id.expansion_key, id.number))
        index2_path = data_directory.joinpath(id.expansion, self._INDEX2_FILE_FORMAT.format(id.type_key, id.expansion_key, id.number))
        if index_path.exists() and index_path.is_file():
            self._source = IndexSource(self, Index(id, index_path.as_posix()))
        elif index2_path.exists() and index2_path.is_file():
            self._source = Index2Source(self, Index2(id, index2_path.as_posix()))
        else:
            raise FileNotFoundError

    def get_data_stream(self, dat_file=0) -> IO:
        thread = threading.get_ident()

        key = (thread, dat_file)
        with self._data_streams_lock:
            stream = self._data_streams.get(key, None)

        if stream is not None:
            return stream

        base_name = self._DAT_FILE_FORMAT.format(self.id.type_key, self.id.expansion_key, self.id.number, dat_file)
        full_path = self.data_directory.joinpath(self.id.expansion, base_name)

        if self.keep_in_memory:
            if dat_file not in self._buffers:
                logger.info('Reading: %s' % full_path)
                self._buffers[dat_file] = full_path.read_bytes()
            stream = io.BufferedReader(self._buffers[dat_file])
        else:
            logger.info('Opening: %s' % full_path)
            stream = full_path.open(mode='rb')

        with self._data_streams_lock:
            self._data_streams[key] = stream

        return stream

    def __str__(self):
        return "%s/%02x%02x%02x" % (self.id.expansion, self.id.type_key, self.id.expansion_key, self.id.number)

    def file_exists(self, path):
        return self.source.file_exists(path)

    def get_file(self, path):
        return self.source.get_file(path)

    def __iter__(self):
        return iter(self.source)
