import sys
from queue import Queue, Empty
from time import sleep
from threading import Thread

from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.Qt import Qt
import PyQt5.QtWebEngineWidgets

from .Utils import Counter, err_catch

_call_counter = Counter()
_call_queue: Queue[tuple[int, callable, tuple, dict]] = Queue()
_return_status: dict[int, bool] = dict()
_return_data: dict[int, any] = dict()
_default_interval = 0.01

float_key = Qt.FramelessWindowHint | Qt.Tool


class FloatWidget(QWidget):
    allow_frameless = False

    def __init__(self):
        super().__init__()
        self._old_move_pos = None
        self._old_resize_pos = None
        self._float_lock = False
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        if self.allow_frameless:
            self.setWindowFlags(self.windowFlags() | float_key)
        # self.setAttribute(Qt.WA_TranslucentBackground, True)

    @err_catch
    def is_frameless(self):
        return self.windowFlags() & float_key

    @err_catch
    def is_float_locked(self):
        return self._float_lock

    @err_catch
    def float_lock(self):
        if self.is_float_locked(): return
        self._float_lock = True
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    @err_catch
    def float_unlock(self):
        if self.is_float_locked(): return
        self._float_lock = False
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    @err_catch
    def mousePressEvent(self, QMouseEvent):
        if self._float_lock: return
        if QMouseEvent.button() == Qt.RightButton and self.allow_frameless:
            self.switch_frameless()
        if QMouseEvent.button() == Qt.LeftButton:
            mpos = QMouseEvent.pos()
            if self.width() + self.height() - mpos.x() - mpos.y() < 35:
                self._old_resize_pos = QMouseEvent.globalPos()
            else:
                self._old_move_pos = QMouseEvent.globalPos()

    @err_catch
    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            self._old_move_pos = None
            self._old_resize_pos = None

    @err_catch
    def switch_frameless(self):
        self.setWindowFlags(self.windowFlags() ^ float_key)
        self.show()

    @err_catch
    def mouseMoveEvent(self, event):
        if self._old_move_pos is not None:
            delta = QPoint(event.globalPos() - self._old_move_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_move_pos = event.globalPos()
        if self._old_resize_pos is not None:
            delta = QPoint(event.globalPos() - self._old_resize_pos)
            self.resize(self.width() + delta.x(), self.height() + delta.y())
            self._old_resize_pos = event.globalPos()

    @err_catch
    def full_close(self):
        self.hide()
        self.disconnect()
        self.deleteLater()


def _process_func_queue():
    try:
        call_id, func, args, kwargs = _call_queue.get(False)
    except Empty:
        return
    try:
        _return_data[call_id] = func(*args, **kwargs)
    except Exception as e:
        _return_data[call_id] = e
    finally:
        _return_status[call_id] = False


def ui_loop_exec(func, *args, **kwargs):
    call_id = _call_counter.get()
    _return_status[call_id] = True
    _call_queue.put((call_id, func, args, kwargs))
    while _return_status[call_id]:
        sleep(_default_interval)
    res = _return_data[call_id]
    del _return_status[call_id]
    del _return_data[call_id]
    if isinstance(res, Exception): raise res
    return res


def ui_loop_call(func):
    def warper(*args, **kwargs):
        return ui_loop_exec(func, *args, **kwargs)

    return warper


class _QtThread(Thread):
    app: QApplication
    timer: QTimer

    def run(self):
        self.app = QApplication(sys.argv)
        self.timer = QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(_process_func_queue)
        self.timer.start()
        self.app.exec_()


def close_thread():
    if _main_thread.is_alive():
        _main_thread.app.exit()
        _main_thread.join()
        return True
    return False


def start_thread():
    global _main_thread
    if not _main_thread.is_alive():
        _main_thread = _QtThread()
        _main_thread.start()
        return True
    return False


_main_thread: _QtThread = _QtThread()
_main_thread.start()
