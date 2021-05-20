import asyncio
import aiohttp
from traceback import format_exc
from FFxivPythonTrigger import PluginBase, process_event, EventBase


class ACTLogEvent(EventBase):
    id = "act log line"

    def __init__(self, raw: str):
        self.raw = raw

    def text(self):
        return self.raw


class ACTLogLines(PluginBase):
    name = 'ACT Log Lines'

    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.port = self.storage.data.setdefault('port', 3521)
        self.host = self.storage.data.setdefault('host', '127.0.0.1')
        self.storage.save()
        self.work = False
        self.ws = None

    def url(self):
        return 'ws://%s:%s' % (self.host, self.port)

    async def _plugin_start(self):
        client = aiohttp.ClientSession()
        while self.work:
            try:
                self.ws = await client.ws_connect(self.url())
                break
            except aiohttp.ClientConnectorError:
                await asyncio.sleep(3)
            except Exception:
                self.logger.error("error occurred while connecting to act server, \n" + format_exc())
                self.work = False
        if self.ws is not None:
            self.logger.info("connect to act server success")
            while self.work:
                msg = await self.ws.receive()
                if msg.type == aiohttp.WSMsgType.text:
                    process_event(ACTLogEvent(msg.data))
                elif msg.type == aiohttp.WSMsgType.closed:
                    self.logger.info("server closed")
                    break
                elif msg.type == aiohttp.WSMsgType.error:
                    self.logger.info("error occurred")
                    break
            await self.ws.close()
            self.ws = None

    def _onunload(self):
        self.work = False
        if self.ws is None:
            asyncio.set_event_loop(self.loop)
            if self.ws is not None:
                self.loop.run_until_complete(self.ws.close())

    def _start(self):
        asyncio.set_event_loop(self.loop)
        self.work = True
        while self.work:
            self.loop.run_until_complete(self._plugin_start())
