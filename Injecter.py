import argparse
import sys

endl = "\n<press enter to exit>"
if sys.version_info < (3, 9):
    input("please use python environment >=3.9" + endl)
    exit()
parser = argparse.ArgumentParser(description='using to inject FFxivPythonTrigger to a game process')
parser.add_argument('-p', '--pid', type=int, nargs='?', default=None, metavar='PID', help='pid of process to inject')
parser.add_argument('-o', '--port', type=int, nargs='?', default=3520, metavar='Port', help='port of the socket logger')
parser.add_argument('-d', '--dataDir', type=str, nargs='?', default="AppData", metavar='Directory', help='directory of fpt data')
parser.add_argument('-n', '--pName', nargs='?', default="ffxiv_dx11.exe", metavar='Process Name', help='name of process find to inject')
parser.add_argument('-e', '--entrance', nargs='?', default="Entrance.py", metavar='File Name', help='entrance file of FFxivPythonTrigger')
parser.add_argument('-sr', dest='skip_requirement_check', action='store_const', const=True, default=False, help='skip the requirement check')
parser.add_argument('-fs', dest='force_search_address', action='store_const', const=True, default=False, help='force address manager search')
args = parser.parse_args(sys.argv[1:])
if not args.skip_requirement_check:
    from FFxivPythonTrigger import requirements_controller

    requirements = [i for i in open('requirements.txt', mode='r').read().split('\n') if i]
    if not requirements_controller.test_requirements(requirements):
        if requirements_controller.pip_source is None:
            input("no valid pip source" + endl)
            exit()
        print('use pypi source [%s]' % requirements_controller.pip_source_name)
        requirements_controller.install(*requirements)
        if not requirements_controller.test_requirements(requirements):
            input("cant install requirements" + endl)
            exit()

from FFxivPythonTrigger.memory.res import kernel32, structure
from FFxivPythonTrigger.memory import process, memory
import locale
import os
from json import dumps
import _thread
import socket
import time
import ctypes

try:
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
except:
    is_admin = False
if not is_admin:
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    exit()
ep = process.enable_privilege()
if ep:
    input(f"enable privileges failed with err code {ep}" + endl)
    exit()

# find the python library
python_version = "python{0}{1}.dll".format(sys.version_info.major, sys.version_info.minor)
python_lib = process.module_from_name(python_version).filename
print("found python library at :%s" % python_lib)

pid = args.pid
check_time = 0
handler = None

if pid is None:
    print("start searching for game process [%s]..." % args.pName)
    black_list_pid = list()
    while pid is None:
        for p in process.list_processes():
            if args.pName in p.szExeFile.decode(locale.getpreferredencoding()).lower() and p.th32ProcessID not in black_list_pid:
                pid = p.th32ProcessID
                handler = kernel32.OpenProcess(structure.PROCESS.PROCESS_ALL_ACCESS.value, False, pid)
                if not handler:  # if cant open process,skip
                    black_list_pid.append(pid)
                    print(f"can't open process {pid} with error {ctypes.windll.kernel32.GetLastError()}")
                    pid = None
                    continue
                if process.module_from_name(python_version, handler):  # if the process is already injected by python, skip
                    black_list_pid.append(pid)
                    print(f"process {pid} has been injected")
                    pid = None
                    continue
                break
        check_time += 1
        time.sleep(1)
else:
    handler = kernel32.OpenProcess(structure.PROCESS.PROCESS_ALL_ACCESS.value, False, pid)
    if not handler:
        input(f"could not open process {pid}" + endl)
        exit()

print("game process pid: %s" % pid)
if check_time: time.sleep(3)

python_lib_h = process.inject_dll(bytes(python_lib, 'utf-8'), handler)
if not python_lib_h:
    input("inject failed" + endl)
    exit()
print("inject python environment success")

local_handle = kernel32.GetModuleHandleW(python_version)

dif = python_lib_h - local_handle
funcs = {k: dif + kernel32.GetProcAddress(local_handle, k) for k in [b'Py_InitializeEx', b'PyRun_SimpleString', b'Py_FinalizeEx']}
print("search calling address success")

param_addr = memory.allocate_memory(4, handler)
memory.write_memory(ctypes.c_int, param_addr, 1, handler)
process.start_thread(funcs[b'Py_InitializeEx'], param_addr, handler)

print("initialize ingame python environment success")
application_path = ""
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)
else:
    input("application_path not found" + endl)
    exit()

err_path = os.path.join(application_path, 'InjectErr.log').replace("\\", "\\\\")
sys.path.insert(0, application_path)
game_environ = {
    'FptSocketPort': str(args.port),
    'FptDataDir': str(args.dataDir),
    'address_search': "1" if args.force_search_address else "",
}
shellcode = f"""
import sys
import os
from os import chdir,environ
from traceback import format_exc
init_modules = set(sys.modules.keys())
try:
    os.environ|={game_environ}
    sys.path={dumps(sys.path)}
    os.chdir(sys.path[0])
    __import__("{args.entrance.rstrip('.py')}")
except:
    with open("{err_path}", "w+") as f:
        f.write(format_exc())
finally:
    for key in sys.modules.keys():
        if key not in init_modules:
            del sys.modules[key]
"""

shellcode = shellcode.encode('utf-8')

print("shellcode generated, starting to inject shellcode...")
shellcode_addr = memory.allocate_memory(len(shellcode), handler)
written = ctypes.c_ulonglong(0)
memory.write_bytes(shellcode_addr, shellcode, handler=handler)
_thread.start_new_thread(process.start_thread, (funcs[b'PyRun_SimpleString'], shellcode_addr,), {'handler': handler})
print("shellcode injected, FFxivPythonTrigger should be started in a few seconds")
print("Everything should be ready in a second. If it is not completed within a period of time, please check the log files.")
print(f"waiting for connect at port {args.port}...")
HOST, PORT = "127.0.0.1", args.port
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        sock.connect((HOST, PORT))
        break
    except:
        time.sleep(1)
print("connect!")
while True:
    try:
        size = int.from_bytes(sock.recv(4), 'little', signed=True)
        if size < 0:
            print('end')
            sock.close()
            time.sleep(2)
            break
        else:
            print(sock.recv(size).decode('utf-8'))
    except Exception:
        break
input(endl)
exit()
