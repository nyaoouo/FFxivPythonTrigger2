import socketserver
from FFxivPythonTrigger import PluginBase
from FFxivPythonTrigger import Logger

default_host = "127.0.0.1"
default_port = 3520

connection_pool = []

_logger = Logger.Logger("SocketLogger")


def broadcast_msg(msg):
    data = str(msg).encode('utf-8')
    len_data = len(data).to_bytes(4, byteorder="little",signed=True)
    for connection in connection_pool.copy():
        if connection._closed:
            connection_pool.remove(connection)
        else:
            connection.send(len_data)
            connection.send(data)


def close():
    data = (-1).to_bytes(4, byteorder="little",signed=True)
    for connection in connection_pool.copy():
        if connection._closed:
            connection_pool.remove(connection)
        else:
            connection.send(data)


class TcpServer(socketserver.BaseRequestHandler):
    def handle(self):
        _logger.info("new connection")
        if Logger.PRINT != broadcast_msg:
            _logger.debug("set logger print method")
            Logger.PRINT = broadcast_msg
        for log in Logger.print_history.copy():
            data = str(log).encode('utf-8')
            len_data = len(data).to_bytes(4, byteorder="little")
            self.request.send(len_data)
            self.request.send(data)
        connection_pool.append(self.request)
        while True:
            if not self.request.recv(1):
                break


class SocketLogger(PluginBase):
    name = "socket logger"

    def __init__(self):
        super(SocketLogger, self).__init__()
        self.server_config = self.storage.data.setdefault('server', dict())
        host = self.server_config.setdefault('host', default_host)
        port = self.server_config.setdefault('port', default_port)
        self.server = socketserver.ThreadingTCPServer((host, port), TcpServer)
        self.server.allow_reuse_address = True
        self.create_mission(self.server.serve_forever)

    def _onunload(self):
        close()
        self.server.shutdown()
        self.server.server_close()
