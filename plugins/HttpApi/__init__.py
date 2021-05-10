from FFxivPythonTrigger import PluginBase, Logger
from aiohttp import web
import asyncio
import traceback

_logger = Logger.Logger("HttpApi")

default_host = "127.0.0.1"
default_port = 2019


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

        class temp:
            register_post_route = self.register_post_route
            unregister_post_route = self.unregister_post_route

        self.register_api('HttpApi', temp)

    def register_post_route(self, path, controller):
        if path in self.routes:
            raise Exception("%s is already registered" % path)
        _logger.debug("[%s] is registered as a new api"%path)
        self.routes[path] = controller

    def unregister_post_route(self, path):
        if path not in self.routes:
            raise Exception("%s is not registered" % path)
        _logger.debug("[%s] is unregistered"%path)
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

    async def _plugin_onunload(self):
        await self.runner.shutdown()
        await self.runner.cleanup()
        _logger.info("HttpApi server closed")
        self.work = False

    def _onunload(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._plugin_onunload())

    async def _plugin_start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        host = self.server_config.setdefault('host', default_host)
        port = self.server_config.setdefault('port', default_port)
        await web.TCPSite(self.runner, host, port).start()
        _logger.info("HttpApi Server started on http://%s:%s" % (host, port))
        self.work = True
        while self.work:
            await asyncio.sleep(1)

    def _start(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._plugin_start())
