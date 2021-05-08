import re
from typing import Union
import time

line_regex = re.compile(r"^/(?P<command>\S+)\s+(?P<args>\S.*)$")
if_statement_regex = re.compile(r'^\[(?P<statement>.+)]\s+(?P<arg>[^|]+)$')
if_else_statement_regex = re.compile(r'^\[(?P<statement>.+)]\s+(?P<arg>[^|]+)\s+\|\s+(?P<arg2>.*)$')
find_wait_regex = re.compile(r"(?P<args>\S.*?)(?:\s+<wait\.(?P<wait>\d+(?:\.\d+)?)>)?$")

output_format = '/{command} {arg}'


class MacroLine(object):
    def get_output(self, params: dict[str, any]) -> tuple[str, str, float]: pass


def find_wait(arg: str):
    temp = find_wait_regex.search(arg)
    return temp.group('args'), temp.group('wait')


class CommonMacroLine(MacroLine):
    def __init__(self, command, arg):
        self.command = command
        self.arg, sleep = find_wait(arg)
        self.sleep = float(sleep) if sleep else 0

    def get_output(self, params: dict[str, any]) -> tuple[str, str, float]:
        return self.command, self.arg.format(**params), self.sleep


class IfMacroLine(MacroLine):
    def __init__(self, command: str, statement: str, arg: str):
        self.command = command
        self.statement = statement
        self.arg, sleep = find_wait(arg)
        self.sleep = float(sleep) if sleep else 0

    def get_output(self, params: dict[str, any]) -> tuple[str, str, float]:
        if eval(self.statement, None, params):
            return self.command, self.arg.format(**params), self.sleep
        else:
            return '', '', -1


class IfElseMacroLine(MacroLine):
    def __init__(self, command: str, statement: str, arg: str, arg2: str):
        self.command = command
        self.statement = statement
        self.arg, sleep = find_wait(arg)
        self.sleep = float(sleep) if sleep else 0
        self.arg2, sleep = find_wait(arg2)
        self.sleep2 = float(sleep) if sleep else 0

    def get_output(self, params: dict[str, any]) -> tuple[str, str, float]:
        if eval(self.statement, None, params):
            return self.command, self.arg.format(**params), self.sleep
        else:
            return self.command, self.arg2.format(**params), self.sleep2


class LabelMacroLine(MacroLine):
    def __init__(self, arg):
        self.arg = arg


def line_parse(line: str) -> Union[MacroLine, None]:
    line = line.split("#")[0].strip()
    temp = line_regex.match(line)
    if not temp: return
    command = temp.group('command')
    args = temp.group('args')
    if command == "label":
        return LabelMacroLine(args)
    temp = if_statement_regex.match(args)
    if temp:
        return IfMacroLine(command, temp.group('statement'), temp.group('arg'))
    else:
        temp = if_else_statement_regex.match(args)
        if temp:
            return IfElseMacroLine(command, temp.group('statement'), temp.group('arg'), temp.group('arg2'))
        else:
            return CommonMacroLine(command, args)


class MacroFinish(Exception):
    pass


class Macro(object):
    def __init__(self, macro_str: str):
        self.macros = list()
        self.labels = dict()
        for line in macro_str.split("\n"):
            macro = line_parse(line)
            if type(macro) == LabelMacroLine:
                self.labels[macro.arg] = len(self.macros)
                macro = None
            self.macros.append(macro)

    def get_runner(self):
        return MacroRunner(self.macros, self.labels)


class MacroRunner(object):
    def __init__(self, macros: list[MacroLine], labels: dict[str, int]):
        self.current_line = 0
        self.macros = macros
        self.labels = labels

    def get_output(self, line: int, param):
        return self.macros[line].get_output(param) if self.macros[line] is not None else ("", "", -1.0)

    def next(self, param) -> tuple[str, str, float]:
        if self.current_line >= len(self.macros):
            raise MacroFinish()
        cmd, arg, sleep = self.get_output(self.current_line, param)
        while not cmd:
            self.current_line += 1
            if self.current_line >= len(self.macros):
                raise MacroFinish()
            cmd, arg, sleep = self.get_output(self.current_line, param)
        self.current_line += 1
        if cmd == "jmp":
            try:
                self.current_line = self.labels[arg]
            except KeyError:
                self.current_line = int(arg)
            cmd, arg, sleep_t = self.next(param)
            return cmd, arg, sleep_t + sleep
        return cmd, arg, sleep

    def run(self, param, call):
        try:
            while True:
                cmd, arg, sleep = self.next(param)
                call(cmd, arg)
                time.sleep(sleep)
        except MacroFinish:
            pass


if __name__ == '__main__':
    command = """
#a test macro
/ac happy
/play [status=="happy"] game <wait.1>
/eat [money>10] sandwiches <wait.1.5> | cup cake # an if else statement for common command
/jmp [status=="happy"] a | b # an if else statement for jump
/label a
/ac {status}:laugh
/jmp c
/label b
/ac {status}:cry
/jmp c
/label c
/ac end
"""
    o = lambda command, arg: print(output_format.format(arg=arg, command=command))
    Macro(command).get_runner().run({'status': 'happy', 'money': 9}, o)
    Macro(command).get_runner().run({'status': 'sad', 'money': 15}, o)
