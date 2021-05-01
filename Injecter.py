from FFxivPythonTrigger.memory.res import kernel32, structure
from FFxivPythonTrigger.memory import process, memory
import ctypes
import locale
import sys
import os
from json import dumps
import _thread
import socket
import time

try:
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
except:
    is_admin = False
if not is_admin:
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, sys.argv[0], None, 1)
    exit()

endl = "\n<press enter to exit>"

name = "ffxiv_dx11.exe"
pid = None
print("start searching for game process...")
while pid is None:
    for p in process.list_processes():
        if name in p.szExeFile.decode(locale.getpreferredencoding()).lower():
            pid = p.th32ProcessID
            break
    time.sleep(1)
print("game process pid: %s" % pid)
time.sleep(3)
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
        print("inject failed" + endl)
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
    exec(open("%s").read())
except:
    with open("%s", "w+") as f:
        f.write(format_exc())
finally:
    for key in sys.modules.keys():
        if key not in init_modules:
            del sys.modules[key]
""" % (
    dumps(sys.path),
    'Entrance.py',
    err_path
)

shellcode = shellcode.encode('ascii')
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
    except:
        break
process.start_thread(funcs[b'Py_FinalizeEx'], handler=handler)
