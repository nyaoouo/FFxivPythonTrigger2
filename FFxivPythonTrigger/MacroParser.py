import re
from typing import Union, Optional
import time

line_regex = re.compile(r"^/(?P<command>\S+)\s+(?P<args>\S.*)$")
if_statement_regex = re.compile(r'^\[(?P<statement>.+)]\s+(?P<arg>.+)$')
find_wait_regex = re.compile(r"(?P<args>\S.*?)(?:\s+<wait\.(?P<wait>\d+(?:\.\d+)?)>)?$")


class MacroFinish(Exception):
    pass


class MacroArg(object):
    def __init__(self, raw_str: str):
        temp = find_wait_regex.search(raw_str)
        raw_str, self.wait = temp.group('args'), float(temp.group('wait') if temp.group('wait') is not None else 0)
        self.use_eval = raw_str.startswith("*") and raw_str.endswith("*")
        self.raw_str = raw_str.strip("*") if self.use_eval else raw_str

    def __str__(self):
        return self.raw_str

    def get_output(self, params: dict[str, any]) -> tuple[str, float]:
        if self.use_eval:
            return eval(self.raw_str, None, params), self.wait
        else:
            return self.raw_str.format(**params).strip(), self.wait


class IfMacroArg(object):
    def __init__(self, statement: str, raw_str: str):
        self.statement = statement
        self.arg = MacroArg(raw_str)

    def __str__(self):
        return str(self.arg)

    def get_output(self, params: dict[str, any]) -> Optional[tuple[str, float]]:
        if eval(self.statement, None, params):
            return self.arg.get_output(params)


class MacroLine(object):
    args: list[Union[MacroArg, IfMacroArg]]
    cmd: str

    def __init__(self, cmd: str, args: str):
        self.cmd = cmd
        self.args = []
        for raw_arg in args.split('|'):
            temp = if_statement_regex.match(raw_arg.strip())
            self.args.append(IfMacroArg(temp.group('statement'), temp.group('arg')) if temp else MacroArg(raw_arg))

    def get_label(self):
        return str(self.args[0])

    def get_output(self, params: dict[str, any]) -> tuple[str, str, float]:
        for arg in self.args:
            ans = arg.get_output(params)
            if ans is not None:
                return self.cmd, ans[0], ans[1]
        return "", "", 0


def line_parse(line: str) -> Optional[MacroLine]:
    temp = line_regex.match(line.split("#")[0].strip())
    if temp: return MacroLine(temp.group('command'), temp.group('args'))


class Macro(object):
    def __init__(self, macro_str: str):
        self.macros = list()
        self.labels = dict()
        for line in macro_str.split("\n"):
            macro = None
            temp = line_regex.match(line.split("#")[0].strip())
            if temp:
                if temp.group('command') == "label":
                    self.labels[temp.group('args').strip()] = len(self.macros)
                else:
                    macro = MacroLine(temp.group('command'), temp.group('args'))
            self.macros.append(macro)

    def get_runner(self):
        return MacroRunner(self.macros, self.labels)


class MacroRunner(object):
    def __init__(self, macros: list[MacroLine], labels: dict[str, int]):
        self.current_line = 0
        self.macros = macros
        self.labels = labels

    def get_output(self, line: int, param) -> tuple[str, str, float]:
        return self.macros[line].get_output(param) if self.macros[line] is not None else ("", "", 0)

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
        elif cmd.startswith("set_") and len(cmd) > 4:
            param[cmd.split("_", 1)[1]] = arg
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
/say start!
/play [status=="happy"] game <wait.1>
/set_money *money*2*
/eat [money>20] sandwiches <wait.1.5> | cup cake
/jmp [status=="happy"] a | [status=="sad"] b | d
/label a
/say {status}:laugh
/jmp c
/label b
/say {status}:cry
/jmp c
/label d
/say *f"{status}:play game"*
/set_status happy!!
/say {status} now!
/jmp c
/label c
/ac end
"""
    output_format = '/{command} {arg}'
    o = lambda command, arg: print(output_format.format(arg=arg, command=command))
    Macro(command).get_runner().run({'status': 'happy', 'money': 9}, o)
    print()
    Macro(command).get_runner().run({'status': 'sad', 'money': 15}, o)
    print()
    Macro(command).get_runner().run({'status': 'boring', 'money': 15}, o)
