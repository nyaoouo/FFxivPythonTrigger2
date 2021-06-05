import socket
import time
import argparse
import sys

parser = argparse.ArgumentParser(description='this is a script to just act as an terminal of socket logger')
parser.add_argument('-o', '--port', type=int, nargs='?', default=3520, metavar='Port', help='port of the socket logger')

HOST, PORT = "127.0.0.1", parser.parse_args(sys.argv[1:]).port
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
