from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger import frame_inject
from .AddressManager import do_action_func_addr, action_manager_addr, do_action_location_addr
from ctypes import *
_logger = Logger()

_do_action_func = CFUNCTYPE(c_int64, c_int64, c_uint, c_uint, c_int64, c_uint, c_uint, c_int)(do_action_func_addr)

_do_action_location_func = CFUNCTYPE(c_char, c_int64, c_uint, c_uint, c_int64, c_int64, c_uint)(do_action_location_addr)


def do_action(action_type, action_id, target_id=0xE0000000, unk1=0, unk2=0, unk3=0):
    frame_inject.register_once_call(_do_action_func, action_manager_addr, action_type, action_id, target_id, unk1, unk2, unk3)
    # return _do_action_func(action_sub_addr, action_type, action_id, target_id, unk1, unk2, unk3)


class Vector3(Structure):
    _fields_ = [('x', c_float), ('z', c_float), ('y', c_float)]


def _do_action_location(action_type, action_id, x: float, y: float, z: float, target_id=0xE0000000):
    location_data = Vector3(x=x, y=y, z=z)
    _do_action_location_func(action_manager_addr, action_type, action_id, target_id, addressof(location_data), 0)


def do_action_location(action_type, action_id, x: float, y: float, z: float, target_id=0xE0000000):
    frame_inject.register_once_call(_do_action_location, action_type, action_id, x, y, z, target_id)


def use_skill(skill_id, target_id=0xE0000000):
    return do_action(1, skill_id, target_id)


def use_item(item_id, target_id=0xE0000000, block_id=65535):
    return do_action(2, item_id, target_id, block_id)


def ride_mount(mount_id):
    return do_action(13, mount_id)


def call_minion(minion_id):
    return do_action(8, minion_id)


def fashion_item(item_id):
    return do_action(20, item_id)


def common_skill_id(skill_id, target_id=0xE0000000):
    return do_action(5, skill_id, target_id)


def craft_action(action_id):
    return do_action(9, action_id)
