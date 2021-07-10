import json
import os
from ctypes import c_float, c_int, c_bool, CFUNCTYPE, c_ubyte, c_int64, c_uint
from json import JSONDecodeError

from aiohttp import web

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_address, read_memory, scan_pattern
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

command = "@WayMarks"
marking_controller_sig = "48 8D ? ? ? ? ? 41 B0 ? E8 ? ? ? ? 85 C0"
marking_func_sig = "48 89 5C 24 ?? 48 89 6C 24 ?? 57 48 83 EC ?? 8D 42"


class WayMarkStruct(OffsetStruct({
    'x': (c_float, 0x0),
    'z': (c_float, 0x4),
    'y': (c_float, 0x8),
    '_x': (c_int, 0x10),
    '_z': (c_int, 0x14),
    '_y': (c_int, 0x18),
    'is_active': (c_bool, 0x1c),
})):
    def set(self, x: float = None, y: float = None, z: float = None, is_active: bool = None):
        if x is not None:
            self.x = x
            self._x = int(x * 1000)
        if y is not None:
            self.y = y
            self._y = int(y * 1000)
        if z is not None:
            self.z = z
            self._z = int(z * 1000)
        if is_active is not None:
            self.is_active = is_active

    def get_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'is_active': self.is_active
        }


WayMarksStruct = OffsetStruct({
    'A': (WayMarkStruct, 0x0),
    'B': (WayMarkStruct, 0x20),
    'C': (WayMarkStruct, 0x40),
    'D': (WayMarkStruct, 0x60),
    'One': (WayMarkStruct, 0x80),
    'Two': (WayMarkStruct, 0xA0),
    'Three': (WayMarkStruct, 0xC0),
    'Four': (WayMarkStruct, 0xE0),
})

MarkingFunc = CFUNCTYPE(c_ubyte, c_int64, c_ubyte, c_uint)

MARKING_NAMES = ['attack1', 'attack2', 'attack3', 'attack4', 'attack5', 'bind1', 'bind2',
                 'bind3', 'stop1', 'stop2', 'square', 'circle', 'cross', 'triangle']

MARKINGS = {MARKING_NAMES[i]: i + 1 for i in range(len(MARKING_NAMES))}


def is_valid_way_mark_type(mark_type: str):
    return mark_type in WayMarksStruct.raw_fields


class Markings(PluginBase):
    name = "Markings"
    git_repo = 'nyaoouo/FFxivPythonTrigger2'
    repo_path = 'plugins/Markings'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super(Markings, self).__init__()
        am = AddressManager(self.storage.data, self.logger)
        marking_func = am.get('marking_func', scan_pattern, marking_func_sig)
        self.marking_controller_addr = am.get('marking_controller', scan_address, marking_controller_sig, cmd_len=7)
        self.storage.save()
        self.way_marks = read_memory(WayMarksStruct, self.marking_controller_addr + 432)
        self.marking_func = MarkingFunc(marking_func)
        self.register_api('Markings', type('obj', (object,), {
            'mark_actor': self.mark_actor,
            'place_way_mark': self.place_way_mark,
            'disable_way_mark': self.disable_way_mark,
            'get_way_marks': self.get_way_marks,
        }))
        api.HttpApi.register_post_route('place', self.way_mark_handler)
        api.HttpApi.register_post_route('mark', self.actor_mark_handler)

    def _onunload(self):
        api.HttpApi.unregister_post_route('place')
        api.HttpApi.unregister_post_route('mark')

    def mark_actor(self, mark_type: str, actor_id: int):
        if mark_type not in MARKINGS:
            raise KeyError("[%s] is not a valid mark type" % mark_type)
        self.marking_func(self.marking_controller_addr, MARKINGS[mark_type], actor_id)

    def place_way_mark(self, mark_type: str, x: float, y: float, z: float):
        if not is_valid_way_mark_type(mark_type):
            raise KeyError("[%s] is not a valid mark type" % mark_type)
        getattr(self.way_marks, mark_type).set(x=x, y=y, z=z, is_active=True)

    def disable_way_mark(self, mark_type: str):
        if not is_valid_way_mark_type(mark_type):
            raise KeyError("[%s] is not a valid mark type" % mark_type)
        getattr(self.way_marks, mark_type).set(is_active=False)

    def get_way_marks(self):
        return {
            k: getattr(self.way_marks, k).get_dict()
            for k in WayMarksStruct.raw_fields.keys()
        }

    async def way_mark_handler(self, request: web.Request):
        try:
            data = json.loads(await request.text())
        except JSONDecodeError:
            return web.json_response({'msg': 'failed', 'rtn': 'json error'})
        if type(data) != dict: return web.json_response({'msg': 'failed', 'rtn': 'data should be dictionary'})
        for k, v in data.items():
            if not is_valid_way_mark_type(k) or type(v) != dict: continue
            if "Active" in v and not bool(v["Active"]):
                self.disable_way_mark(k)
            else:
                to_set = dict()
                if "X" in v:
                    try:
                        to_set['x'] = float(v["X"])
                    except ValueError:
                        pass
                if "Y" in v:
                    try:
                        to_set['y'] = float(v["Y"])
                    except ValueError:
                        pass
                if "Z" in v:
                    try:
                        to_set['z'] = float(v["Z"])
                    except ValueError:
                        pass
                self.place_way_mark(k, **to_set)
        return web.json_response({'msg': 'success'})

    async def actor_mark_handler(self, request: web.Request):
        try:
            data = json.loads(await request.text())
        except JSONDecodeError:
            return web.json_response({'msg': 'failed', 'rtn': 'json error'})
        if type(data) != dict: return web.json_response({'msg': 'failed', 'rtn': 'data should be dictionary'})

        if "MarkType" not in data: return web.json_response({'msg': 'failed', 'rtn': 'no mark type found'})
        if data["MarkType"] not in MARKINGS: return web.json_response({'msg': 'failed', 'rtn': 'Invalid MarkType'})

        if "Name" in data:
            target = list(api.XivMemory.actor_table.get_actors_by_name(data["Name"]))
            if not target: return web.json_response({'msg': 'failed', 'rtn': 'actor not found'})
            target = target[0].id
        elif "ActorId" in data:
            target = int(data["ActorId"])
        else:
            return web.json_response({'msg': 'failed', 'rtn': 'no actor found'})
        self.mark_actor(data["MarkType"], target)
        return web.json_response({'msg': 'success'})
