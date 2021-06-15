import sys
import os
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from time import time, sleep, perf_counter
from traceback import format_exc
from typing import List, Type, Dict, Set, Optional
from inspect import isclass, getfile, getsourcelines
import atexit
from importlib import import_module, reload

from . import AttrContainer, Storage, Logger, FrameInject, Sigs, AddressManager

LOG_FILE_SIZE_MAX = 1024 * 1024


class Mission(Thread):
    def __init__(self, name: str, mission_id: int, mission, *args, **kwargs):
        super(Mission, self).__init__(name="%s#%s" % (name, mission_id))
        self.name = name
        self.mission_id = mission_id
        self.mission = mission
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.mission(*self.args, **self.kwargs)
        except Exception:
            _logger.error(f"error occurred in mission {self}:\n{format_exc()}")
        try:
            _missions.remove(self)
        except KeyError:
            pass


class EventBase(object):
    id = 0
    name = "unnamed event"

    def text(self):
        return ""

    def __str__(self):
        return f"<{self.name}>{self.text()}"


class EventCallback(object):
    def __init__(self, plugin, call, limit_sec=None):
        self.plugin = plugin
        self._call = call
        self.limit_sec = limit_sec

    def call(self, event: EventBase):
        if self.limit_sec is not None:
            self.plugin.create_mission(self._call, event, self.limit_sec)
        else:
            self.plugin.create_mission(self._call, event)


class PluginBase(object):
    name = "unnamed_plugin"
    main_mission: Optional[Mission]

    def __init__(self):
        self._events = list()
        self._apis = list()
        self._mission_count = 0
        self._missions = list()
        self._lock = Lock()
        self.main_mission = None
        self.logger = Logger.Logger(self.name)
        self.storage = Storage.get_module_storage(self.name)

    def create_mission(self, call, *args, limit_sec=0.1, **kwargs) -> Mission:
        def temp(*_args, **_kwargs):
            start = perf_counter()
            try:
                call(*_args, **_kwargs)
            except Exception:
                self.logger.error("error occurred in mission:" + format_exc())
            if limit_sec > 0:
                used = perf_counter() - start
                if used > limit_sec:
                    self.logger.warning("[{}:{}] run for {:2f}s".format(getfile(call), getsourcelines(call)[1], used))

        with self._lock:
            mId = self._mission_count
            self._mission_count += 1
        mission = Mission(self.name, mId, temp, *args, **kwargs)
        if append_missions(mission):
            self._missions.append(mission)
        return mission

    def register_api(self, name: str, api_object: any):
        self._apis.append(name)
        api.register(name, api_object)

    def register_event(self, event_id, call, limit_sec=None):
        callback = EventCallback(self, call, limit_sec)
        self._events.append((event_id, callback))
        register_event(event_id, callback)

    def p_start(self):
        self.main_mission = self.create_mission(self._start, limit_sec=0)

    def p_unload(self):
        for event_id, callback in self._events:
            unregister_event(event_id, callback)
        for name in self._apis:
            api.unregister(name)
        self._onunload()
        for mission in self._missions:
            try:
                mission.join(-1)
            except RuntimeError:
                pass
        self.storage.save()

    def _onunload(self):
        pass

    def _start(self):
        pass


def log_writer() -> None:
    with open(_log_path, 'a+') as fo:
        while _log_work:
            if _log_write_buffer.empty():
                fo.flush()
            fo.write(str(_log_write_buffer.get()))
            fo.write('\n')


def register_modules(modules: list) -> None:
    for module in modules:
        register_module(module)


def register_module(module) -> List[PluginBase]:
    installed = []
    if type(module) == str:
        _logger.debug("try load plugin \"%s\" dynamically" % module)
        try:
            module = import_module(module)
        except Exception:
            _logger.error('error occurred during import module:\" %s\"' % module)
            _logger.error('error trace:\n' + format_exc())
            raise Exception("module import error")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isclass(attr) and issubclass(attr, PluginBase) and attr != PluginBase:
            installed.append(register_plugin(attr))
    return installed


def unload_module(module):
    if type(module) == str:
        module = import_module(module)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isclass(attr) and issubclass(attr, PluginBase) and attr != PluginBase:
            unload_plugin(attr.name)


def reload_module(module):
    if type(module) == str:
        module = import_module(module)
    unload_module(module)
    module_name = module.__name__
    for sub_module in list(sys.modules.keys()):
        if sub_module.startswith(module_name):
            try:
                reload(import_module(sub_module))
            except ModuleNotFoundError:
                continue
    for plugin in register_module(import_module(module_name)):
        plugin.p_start()


def register_plugin(plugin: Type[PluginBase]) -> PluginBase:
    if plugin.name in _plugins:
        raise Exception("Plugin %s was already registered" % plugin.name)
    _logger.debug("register plugin [start]: %s" % plugin.name)
    try:
        _plugins[plugin.name] = plugin()
    except:
        _logger.error('error occurred during plugin initialization: %s' % plugin.name)
        _logger.error('error trace:\n' + format_exc())
        raise Exception('plugin initialization error')
    _logger.info("register plugin [success]: %s" % plugin.name)
    return _plugins[plugin.name]


def register_event(event_id: any, callback: EventCallback) -> None:
    if event_id not in _events:
        _events[event_id] = set()
    _events[event_id].add(callback)


def unregister_event(event_id: any, callback: EventCallback):
    try:
        _events[event_id].remove(callback)
        if not _events[event_id]:
            del _events[event_id]
    except KeyError:
        pass


def process_event(event: EventBase):
    if event.id in _events or '*' in _events:
        append_missions(Mission("event", 0, _process_event, event))


def _process_event(event: EventBase):
    # _logger.debug("process event [%s]"%event.id)
    if event.id in _events:
        for callback in _events.get(event.id).copy():
            callback.call(event)
    if '*' in _events:
        for callback in _events.get('*').copy():
            callback.call(event)


def unload_plugin(plugin_name):
    _logger.debug("unregister plugin [start]: %s" % plugin_name)
    try:
        _plugins[plugin_name].p_unload()
        del _plugins[plugin_name]
        _logger.info("unregister plugin [success]: %s" % plugin_name)
    except Exception:
        _logger.error('error occurred during unload plugin\n %s' % format_exc())


def list_plugin_names():
    return list(_plugins.keys())


def close():
    _allow_create_missions = False
    for name in reversed(list(_plugins.keys())):
        unload_plugin(name)
    _storage.save()
    if frame_inject is not None and frame_inject.is_installed:
        frame_inject.uninstall()


def append_missions(mission: Mission, guard=True):
    if _allow_create_missions:
        if guard: _missions.add(mission)
        mission.start()
        return True
    return False


def start():
    for plugin in _plugins.values():
        plugin.p_start()
    if _missions:
        _logger.info('FFxiv Python Trigger started')
        while _missions:
            sleep(0.1)
        _logger.info('FFxiv Python Trigger closed')
    else:
        _logger.info('FFxiv Python Trigger closed (no mission is found)')
    alive_missions = [m for m in _missions if m.is_alive()]
    if _plugins or alive_missions:
        _logger.error('above item havn\'t cleared, try again')
        for plugin in _plugins.values():
            _logger.error("plugin: " + plugin.name)
        for mission in alive_missions:
            _logger.error("mission: " + str(mission))
        close()
    global _log_work
    _log_work = False
    _log_mission.join()


def add_path(path: str):
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.insert(0, path)
        if path not in _storage.data['paths']:
            _storage.data['paths'].append(path)
            _storage.save()


LOG_FILE_FORMAT = 'log_{int_time}.txt'
STORAGE_DIRNAME = "Core"
LOGGER_NAME = "Main"

api = AttrContainer.AttrContainer()

_storage = Storage.ModuleStorage(Storage.BASE_PATH / STORAGE_DIRNAME)
_logger = Logger.Logger(LOGGER_NAME)
_log_path = _storage.path / LOG_FILE_FORMAT.format(int_time=int(time()))
_log_work = True
_log_write_buffer = Queue()
_log_mission = Mission('logger', -1, log_writer)
_log_mission.start()

Logger.log_handler.add((Logger.DEBUG, _log_write_buffer.put))
atexit.register(close)

_plugins: Dict[str, PluginBase] = dict()
_missions: Set[Mission] = set()
_events: Dict[any, Set[EventCallback]] = dict()
_allow_create_missions: bool = True

_am = AddressManager.AddressManager(_storage.data.setdefault('address', dict()), _logger)
frame_inject = FrameInject.FrameInjectHook(_am.get("frame_inject", **Sigs.frame_inject))
_storage.save()

frame_inject.install()
frame_inject.enable()

plugin_path = Path(os.getcwd()) / 'plugins'
plugin_path.mkdir(exist_ok=True)
sys.path.insert(0, str(plugin_path))
for path in _storage.data.setdefault('paths', list()):
    _logger.debug("add plugin path:%s" % path)
    sys.path.insert(0, path)
_storage.save()
