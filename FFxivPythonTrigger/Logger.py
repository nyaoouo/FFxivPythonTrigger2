from inspect import getmodule, stack
from typing import Dict, Set, Callable, Tuple, Annotated, List
from datetime import datetime
from threading import Lock


class ModuleExistsException(Exception):
    def __init__(self, module_name: str):
        super(ModuleExistsException, self).__init__("module [%s] is already exists as logger" % module_name)


class ModuleTypeException(Exception):
    def __init__(self, module: any):
        super(ModuleTypeException, self).__init__("module type [%s] is an invalid logger module type" % module)


class Logger(object):
    _module: str

    def __delete__(self, instance):
        _logger_modules.remove(self._module)

    def __init__(self, module_name: str = None):
        """
        create a logger to log with a given module name (or auto generated name)(each module name should be unique)

        :param module_name: (optional) used module name
        """
        if module_name is None:
            module_name = getmodule(stack()[1][0]).__name__
        if type(module_name) != str:
            raise ModuleTypeException(module_name)
        if module_name in _logger_modules:
            raise ModuleExistsException(module_name)
        self._module = module_name

    def log(self, level: int, *messages: any) -> None:
        """
        log a message~

        :param level: level of the log
        :param messages: the message elements to be logged
        """
        log(level, self._module, *messages)

    def debug(self, *messages: any) -> None:
        """
        used for debug only, should not used by user

        :param messages: the message elements to be logged
        """
        self.log(DEBUG, *messages)

    def info(self, *messages: any) -> None:
        """
        let the user know what happens

        :param messages: the message elements to be logged
        """
        self.log(INFO, *messages)

    def warning(self, *messages: any) -> None:
        """
        some thing has gone wrong, but the program is still running

        :param messages: the message elements to be logged
        """
        self.log(WARNING, *messages)

    def error(self, *messages: any) -> None:
        """
        some error happen, some function will be affected

        :param messages: the message elements to be logged
        """
        self.log(ERROR, *messages)

    def critical(self, *messages: any) -> None:
        """
        a fatal error happen, may cause the program to terminate

        :param messages: the message elements to be logged
        """
        self.log(CRITICAL, *messages)


class Log(object):
    level: int
    module: str
    message: str
    datetime: datetime

    def __init__(self, level: int, module: str, message: str):
        self.level = level
        self.module = module
        self.message = message
        self.datetime = datetime.now()

    def header(self):
        return LOG_HEADER_FORMAT.format(
            time=self.datetime.strftime(TIME_FORMAT)[:-TIME_CUTOFF],
            module=self.module,
            level=_get_level_name(self.level),
        )

    def __str__(self):
        return LOG_FORMAT.format(
            header=self.header(),
            message=self.message,
        )


def _default_log_error_handler(e: Exception) -> None:
    pass


def _get_level_name(level: any) -> str:
    result = _level_name.get(level)
    if result is not None:
        return result
    return "Level %s" % level


def log(level: int, module: str, *messages: any) -> None:
    """
    log a message

    *suggested to use the Logger class instead of this

    :param level: level of the log
    :param module: an identifier of where the log from
    :param messages: the message elements to be logged
    """
    msg_log = Log(level, module, MESSAGES_SEPARATOR.join(map(str, messages)))
    if level >= print_log_level >= 0:
        with _print_lock:
            print_history.append(msg_log)
            for line in msg_log.message.split('\n'):
                PRINT(LOG_FORMAT.format(header=msg_log.header(),message=line))
    for h_lv, handler in log_handler:
        if level >= h_lv:
            try:
                handler(msg_log)
            except Exception as e:
                exception_handler(e)


def debug(module: str, *messages: any) -> None:
    """
    used for debug only, should not used by user

    *suggested to use the Logger class instead of this

    :param module: an identifier of where the log from
    :param messages: the message elements to be logged
    """
    log(DEBUG, module, *messages)


def info(module: str, *messages: any) -> None:
    """
    let the user know what happens

    *suggested to use the Logger class instead of this

    :param module: an identifier of where the log from
    :param messages: the message elements to be logged
    """
    log(INFO, module, *messages)


def warning(module: str, *messages: any) -> None:
    """
    some thing has gone wrong, but the program is still running

    *suggested to use the Logger class instead of this

    :param module: an identifier of where the log from
    :param messages: the message elements to be logged
    """
    log(WARNING, module, *messages)


def error(module: str, *messages: any) -> None:
    """
    some error happen, some function will be affected

    *suggested to use the Logger class instead of this

    :param module: an identifier of where the log from
    :param messages: the message elements to be logged
    """
    log(ERROR, module, *messages)


def critical(module: str, *messages: any) -> None:
    """
    a fatal error happen, may cause the program to terminate

    *suggested to use the Logger class instead of this

    :param module: an identifier of where the log from
    :param messages: the message elements to be logged
    """
    log(CRITICAL, module, *messages)


DEBUG: Annotated[int, "used for debug only, should not used by user"] = 10
INFO: Annotated[int, "let the user know what happens"] = 20
WARNING: Annotated[int, "some thing has gone wrong, but the program is still running"] = 30
ERROR: Annotated[int, "some error happen, some function will be affected"] = 40
CRITICAL: Annotated[int, "a fatal error happen, may cause the program to terminate"] = 50

_level_name: Dict[int, str] = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
}

MESSAGES_SEPARATOR: Annotated[str, "the separator for logger used to connect messages"] = "\t"
LOG_HEADER_FORMAT: Annotated[str, "the format of log header"] = "[{level}]\t[{time}|{module}]\t"
LOG_FORMAT: Annotated[str, "the format of log"] = "{header}\t{message}"
TIME_FORMAT: Annotated[str, "the format of time"] = "%Y-%m-%d %H:%M:%S.%f"
TIME_CUTOFF: Annotated[int, "cutoff the time string"] = 3

PRINT: Annotated[Callable[[any], None], "the method called for print user seen log"] = print
print_log_level: Annotated[int, "if the log level is lower then this, it wont be printed"] = INFO
log_handler: Annotated[Set[Tuple[int, Callable[[Log], None]]], "a set of handler in (handle level, handle method)"] = set()
exception_handler: Annotated[Callable[[Exception], None], "the handler of exceptions happen in log handlers"] = _default_log_error_handler
print_history: Annotated[List[Log], "store the log have printed"] = list()

_logger_modules: Set[str] = set()
_print_lock = Lock()
