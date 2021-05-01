from FFxivPythonTrigger import PluginBase, api
from aiohttp import web
from . import DoTextCommand, DoAction, AddressManager


class Magics(object):
    @staticmethod
    def macro_command(macro):
        DoTextCommand.do_text_command(macro)

    do_action = DoAction

    @staticmethod
    def echo_msg(msg):
        DoTextCommand.do_text_command("/e %s" % msg)


class XivMagic(PluginBase):
    name = "XivMagic"

    async def text_command_handler(self, request: web.Request):
        DoTextCommand.do_text_command(await request.text())
        return web.json_response({'msg': 'success'})

    async def use_item_handler(self, request: web.Request):
        try:
            item_id = int(await request.text())
        except ValueError:
            return web.json_response({'msg': 'Value Error'})
        paths = request.path.split('/')
        if len(paths) > 1 and paths[1] == 'hq':
            item_id += 1000000
        DoAction.use_item(item_id)
        return web.json_response({'msg': 'success'})

    def __init__(self):
        super().__init__()
        self.api_class = Magics()
        self.register_api("Magic", self.api_class)
        api.HttpApi.register_post_route('command', self.text_command_handler)
        api.HttpApi.register_post_route('useitem', self.use_item_handler)

    def _start(self):
        self.api_class.echo_msg("magic started")

    def _unload(self):
        api.HttpApi.unregister_post_route('command')
        api.HttpApi.unregister_post_route('useitem')
