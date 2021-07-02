from aiohttp import web, WSMsgType
import time
import json
from pathlib import Path
from asyncio import CancelledError, new_event_loop, set_event_loop, sleep, run
from FFxivPythonTrigger import PluginBase, api

res = Path(__file__).parent / 'res'

default_host = "127.0.0.1"
default_port = 2020
command = "@WebChat"


class WebChat(PluginBase):
    name = "WebChat"

    async def root_handler(self, request):
        return web.HTTPFound('/index.html')

    async def cmd_deal(self, ws, data):
        if data['a'] == "close":
            await ws.close()
        elif data['a'] == "macro":
            api.Magic.macro_command(data['m'])
        elif data['a'] == "say":
            api.Magic.macro_command("/s %s" % data['m'])
        elif data['a'] == "emote":
            api.Magic.macro_command("/em %s" % data['m'])
        elif data['a'] == "yell":
            api.Magic.macro_command("/y %s" % data['m'])
        elif data['a'] == "shout":
            api.Magic.macro_command("/sh %s" % data['m'])
        elif data['a'] == "tell":
            api.Magic.macro_command("/t %s@%s %s" % (data['t'], data['s'], data['m']))
        elif data['a'] == "alliance":
            api.Magic.macro_command("/a %s" % data['m'])
        elif data['a'] == "freecompany":
            api.Magic.macro_command("/fc %s" % data['m'])
        elif data['a'].startswith("cwlinkshell"):
            api.Magic.macro_command("/cwl%d %s" % (int(data['a'][-1]), data['m']))
        elif data['a'].startswith("linkshell"):
            api.Magic.macro_command("/l%d %s" % (int(data['a'][-1]), data['m']))
        elif data['a'] == "echo":
            api.Magic.macro_command("/e %s" % data['m'])
        elif data['a'] == "party":
            api.Magic.macro_command("/p %s" % data['m'])
        elif data['a'] == "novicenetwork":
            api.Magic.macro_command("/b %s" % data['m'])
        else:
            await ws.send_json({'t': time.time(), 'c': -1, 's': None, 'm': "unknown action [%s]" % data['a']})

    async def ws_handler(self, request):
        ws = web.WebSocketResponse()
        cid = self.client_count
        self.client_count += 1
        self.clients[cid] = ws
        await ws.prepare(request)
        for msg in self.chatLogCache[-200:]:
            await ws.send_json(msg)
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        await self.cmd_deal(ws, json.loads(msg.data))
                    except Exception as e:
                        await ws.send_json({'t': time.time(), 'c': -1, 's': None, 'm': str(e)})
                elif msg.type == WSMsgType.ERROR:
                    pass
        except CancelledError:
            pass
        del self.clients[cid]
        return ws

    def __init__(self):
        super(WebChat, self).__init__()
        self.server_config = self.storage.data.setdefault('server', dict())
        self.app = web.Application()
        self.app.router.add_route('GET', '/', self.root_handler)
        self.app.router.add_route('GET', '/ws', self.ws_handler)
        self.app.router.add_static('/', path=res)
        self.loop = new_event_loop()
        self.clients = dict()
        self.client_count = 0
        self.chatLogCache = []
        self.work = False
        self.runner = None
        self.register_event("log_event", self.deal_chat_log)
        api.command.register(command, self.process_command)

    def deal_chat_log(self, event):
        set_event_loop(self.loop)
        data = {
            't': event.chat_log.timestamp,
            'c': event.channel_id,
            's': event.player,
            'm': event.message
        }
        self.chatLogCache.append(data)
        if len(self.chatLogCache) > 500:
            self.chatLogCache = self.chatLogCache[-200:]
        for cid, client in self.clients.items():
            run(client.send_json(data))

    async def _stop_server(self):
        await self.runner.shutdown()
        await self.runner.cleanup()
        self.logger.info("WebChat server closed")
        self.work = False

    def stop_server(self):
        set_event_loop(self.loop)
        self.loop.create_task(self._stop_server())

    def _onunload(self):
        api.command.unregister(command)
        if self.work:
            self.stop_server()

    async def _start_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        host = self.server_config.setdefault('host', default_host)
        port = self.server_config.setdefault('port', default_port)
        self.storage.save()
        await web.TCPSite(self.runner, host, port).start()
        self.logger.info("WebChat Server started on http://%s:%s" % (host, port))
        self.work = True
        while self.work:
            await sleep(1)

    def start_server(self):
        set_event_loop(self.loop)
        self.loop.run_until_complete(self._start_server())

    def _start(self):
        if self.server_config.setdefault('start_default', False):
            self.start_server()

    def process_command(self, args):
        if args:
            if args[0] == 'start':
                self.server_config['start_default'] = True
                if self.work:
                    api.Magic.echo_msg("WebChat has been started")
                else:
                    if len(args) > 1:
                        self.server_config['port'] = int(args[1])
                    self.create_mission(self.start_server, limit_sec=0)
            elif args[0] == 'close':
                self.server_config['start_default'] = False
                if self.work:
                    self.stop_server()
                else:
                    api.Magic.echo_msg("WebChat haven't been started")
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            api.Magic.echo_msg("WebChat: [%s]" % ('enable' if self.work else 'disable'))
        self.storage.save()
