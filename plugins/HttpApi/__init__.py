from FFxivPythonTrigger import PluginBase, Logger, api
from aiohttp import web
import asyncio
import traceback

_logger = Logger.Logger("HttpApi")

default_host = "127.0.0.1"
default_port = 2019
command = "@HttpApi"


class HttpApiPlugin(PluginBase):
    name = "HttpApi"

    def __init__(self):
        super(HttpApiPlugin, self).__init__()
        self.server_config = self.storage.data.setdefault('server', dict())
        self.app = web.Application()
        self.app.add_routes([web.post('/{uri:.*}', self.post_route)])
        self.loop = asyncio.new_event_loop()
        self.routes = dict()
        self.work = False
        self.runner = None
        api.command.register(command, self.process_command)

        class temp:
            register_post_route = self.register_post_route
            unregister_post_route = self.unregister_post_route

        self.register_api('HttpApi', temp)

    def register_post_route(self, path, controller):
        if path in self.routes:
            raise Exception("%s is already registered" % path)
        _logger.debug("[%s] is registered as a new api" % path)
        self.routes[path] = controller

    def unregister_post_route(self, path):
        if path not in self.routes:
            raise Exception("%s is not registered" % path)
        _logger.debug("[%s] is unregistered" % path)
        del self.routes[path]

    async def post_route(self, request: web.Request):
        paths = request.path.strip('/').split('/')
        if not paths or paths[0] not in self.routes:
            res = web.json_response({'msg': 'resource not found', 'code': 404}, status=404)
        else:
            try:
                res = await self.routes[paths[0]](request)
            except Exception:
                res = web.json_response({'msg': 'server error occurred', 'trace': traceback.format_exc(), 'code': 500}, status=500)
        _logger.debug("request:%s ; response: %s" % (request, res))
        return res

    async def _stop_server(self):
        await self.runner.shutdown()
        await self.runner.cleanup()
        _logger.info("HttpApi server closed")
        self.work = False

    def stop_server(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._stop_server())

    def _onunload(self):
        if self.work:
            self.stop_server()

    async def _start_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        host = self.server_config.setdefault('host', default_host)
        port = self.server_config.setdefault('port', default_port)
        self.storage.save()
        await web.TCPSite(self.runner, host, port).start()
        _logger.info("HttpApi Server started on http://%s:%s" % (host, port))
        self.work = True
        while self.work:
            await asyncio.sleep(1)

    def start_server(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._start_server())

    def _start(self):
        if self.server_config.setdefault('start_default', False):
            self.start_server()

    def process_command(self, args):
        if args:
            if args[0] == 'start':
                self.server_config['start_default']=True
                if self.work:
                    api.Magic.echo_msg("HttpApi has been started")
                else:
                    if len(args) > 1:
                        self.server_config['port'] = int(args[1])
                    self.create_mission(self.start_server)
            elif args[0] == 'close':
                self.server_config['start_default']=False
                if self.work:
                    self.stop_server()
                else:
                    api.Magic.echo_msg("HttpApi haven't been started")
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            api.Magic.echo_msg("HttpApi: [%s]" % ('enable' if self.work else 'disable'))
        self.storage.save()

