from traceback import format_exc
from typing import List, Tuple
from time import perf_counter
from inspect import getfile, getsourcelines, getframeinfo, stack, Traceback

from .Logger import Logger
from .hook import Hook
from ctypes import *

_logger = Logger("Frame Inject")
MISSION_TIME_LIMIT = 0.05


class FrameInjectHook(Hook):
    _continue_works = dict()
    _once_works: List[Tuple[Traceback, callable, tuple, dict]] = list()

    def register_continue_call(self, call, *args, **kwargs):
        self._continue_works[call] = (getframeinfo(stack()[1][0]), args, kwargs)

    def unregister_continue_call(self, call):
        try:
            del self._continue_works[call]
        except KeyError:
            pass

    def register_once_call(self, call, *args, **kwargs):
        self._once_works.append((getframeinfo(stack()[1][0]), call, args, kwargs))

    argtypes = [c_void_p, c_void_p]

    def call(self, caller, call, *args, **kwargs):
        start = perf_counter()
        call(*args, **kwargs)
        use = perf_counter() - start
        if use > MISSION_TIME_LIMIT:
            _logger.warning("frame mission over time {:.2}s (limit:{:.2}s):\n"
                            "at:\t{}:{}\n"
                            "from:\t{}:{}".format(use, MISSION_TIME_LIMIT, getfile(call), getsourcelines(call)[1],caller.filename, caller.lineno))

    def hook_function(self, *oargs):
        try:
            while self._once_works:
                try:
                    caller, call, a, k = self._once_works.pop(0)
                    self.call(caller, call, *a, **k)
                except Exception:
                    _logger.error("error in frame call:\n" + format_exc())
            for c, v in self._continue_works.copy().items():
                try:
                    self.call(v[0], c, *v[1], **v[2])
                except Exception:
                    del self._continue_works[c]
                    _logger.error("error in frame call, continue work will be removed:\n" + format_exc())
        except Exception:
            _logger.error("error in frame inject:\n" + format_exc())
        return self.original(*oargs)
