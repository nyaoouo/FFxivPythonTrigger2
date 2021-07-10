import ctypes.wintypes
import os

from aiohttp import web
import time
from FFxivPythonTrigger import PluginBase, api, window
import win32con


class KeyApi:
    @staticmethod
    def key_down(key_code: int):
        ctypes.windll.user32.SendMessageA(window.CURRENT_HWND, win32con.WM_KEYDOWN, key_code, 0)

    @staticmethod
    def key_up(key_code: int):
        ctypes.windll.user32.SendMessageA(window.CURRENT_HWND, win32con.WM_KEYUP, key_code, 0)

    @staticmethod
    def key_press(key_code: int, time_ms: int = 10):
        KeyApi.key_down(key_code)
        time.sleep(time_ms / 1000)
        KeyApi.key_up(key_code)


class SendKeys(PluginBase):
    name = "SendKeys"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/SendKeys'
    hash_path = os.path.dirname(__file__)

    async def text_command_handler(self, request: web.Request):
        try:
            code = int(await request.text())
            KeyApi.key_press(code)
        except TypeError:
            return web.json_response({
                'msg': 'failed',
                'rtn': 'type error'
            })
        else:
            return web.json_response({
                'msg': 'success',
                'rtn': code
            })

    def __init__(self):
        super().__init__()
        self.api_class = KeyApi()
        self.register_api("SendKeys", self.api_class)
        api.HttpApi.register_post_route('sendkey', self.text_command_handler)

    def _onunload(self):
        api.HttpApi.unregister_post_route('sendkey')
