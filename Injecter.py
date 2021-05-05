from FFxivPythonTrigger.memory.res import kernel32, structure
from FFxivPythonTrigger.memory import process, memory
import locale
import os
from json import dumps
import _thread
import socket
import time
import argparse
import ctypes
import sys

parser = argparse.ArgumentParser(description='using to inject FFxivPythonTrigger to a game process')
parser.add_argument('-p', '--pid', type=int, nargs='?', default=None, metavar='PID', help='pid of process to inject')
parser.add_argument('-n', '--pName', nargs='?', default="ffxiv_dx11.exe", metavar='Process Name', help='name of process find to inject')
parser.add_argument('-e', '--entrance', nargs='?', default="Entrance.py", metavar='File Name', help='entrance file of FFxivPythonTrigger')
args = parser.parse_args(sys.argv[1:])

try:
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
except:
    is_admin = False
if not is_admin:
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    exit()

endl = "\n<press enter to exit>"
pid = args.pid
if pid is None:
    print("start searching for game process [%s]..." % args.pName)
    while pid is None:
        for p in process.list_processes():
            if args.pName in p.szExeFile.decode(locale.getpreferredencoding()).lower():
                pid = p.th32ProcessID
                break
        time.sleep(1)
print("game process pid: %s" % pid)

handler = kernel32.OpenProcess(structure.PROCESS.PROCESS_ALL_ACCESS.value, False, pid)
if not handler:
    input("could not open process" + endl)
    exit()

# find the python library
python_version = "python{0}{1}.dll".format(sys.version_info.major, sys.version_info.minor)
python_lib = process.module_from_name(python_version).filename

# Find or inject python module
python_module = process.module_from_name(python_version, handler)
if python_module:
    python_lib_h = python_module.lpBaseOfDll
else:
    python_lib_h = process.inject_dll(bytes(python_lib, 'ascii'), handler)
    if not python_lib_h:
        input("inject failed" + endl)
        exit()

local_handle = kernel32.GetModuleHandleW(python_version)

dif = python_lib_h - local_handle
funcs = {k: dif + kernel32.GetProcAddress(local_handle, k) for k in [b'Py_InitializeEx', b'PyRun_SimpleString', b'Py_FinalizeEx']}

param_addr = memory.allocate_memory(4, handler)
memory.write_memory(ctypes.c_int, param_addr, 1, handler)
process.start_thread(funcs[b'Py_InitializeEx'], param_addr, handler)

wdir = os.path.abspath('.')
log_path = os.path.join(wdir, 'out.log').replace("\\", "\\\\")
err_path = os.path.join(wdir, 'err.log').replace("\\", "\\\\")
shellcode = """
import sys
from os import chdir
from traceback import format_exc
init_modules = sys.modules.copy()
try:
    sys.path=%s
    chdir(sys.path[0])
    exec(open("%s",encoding='utf-8').read())
except:
    with open("%s", "w+") as f:
        f.write(format_exc())
finally:
    for key in sys.modules.keys():
        if key not in init_modules:
            del sys.modules[key]
""" % (
    dumps(sys.path),
    args.entrance,
    err_path
)

shellcode = shellcode.encode('utf-8')
shellcode_addr = memory.allocate_memory(len(shellcode), handler)
written = ctypes.c_ulonglong(0)
memory.write_bytes(shellcode_addr, shellcode, handler=handler)
_thread.start_new_thread(process.start_thread, (funcs[b'PyRun_SimpleString'], shellcode_addr,), {'handler': handler})

print("waiting for initialization...")
HOST, PORT = "127.0.0.1", 3520
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
