from .struct import Target
from . import AddressManager
from FFxivPythonTrigger.memory import read_memory
from ctypes import pointer


class Targets(Target.Target):
    @property
    def current(self):
        return self._current[0] if self._current else None

    @property
    def mouse_over(self):
        return self._mouse_over[0] if self._mouse_over else None

    @property
    def focus(self):
        return self._focus[0] if self._focus else None

    @property
    def previous(self):
        return self._previous[0] if self._previous else None

    def set_current(self, actor=None):
        self._current = pointer(actor) if actor is not None else None

    def set_focus(self, actor=None):
        self._focus = pointer(actor) if actor is not None else None


targets = read_memory(Targets, AddressManager.target_ptr_addr)
