import traceback
import base64

from FFxivPythonTrigger.memory import *
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger import PluginBase, api, FFxiv_Version

from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, PointerStruct

command = "@zoom"

cam_sig = "48 8D 0D ?? ?? ?? ?? 45 33 C0 33 D2 C6 40 09 01"
cam_collision_jmp_sig = "0F 84 ?? ?? ?? ?? F3 0F 10 54 24 60 F3 0F 10 44 24 64 F3 41 0F 5C D5"
zoom_offset_sig = "F3 0F ?? ?? ?? ?? ?? ?? 48 8B ?? ?? ?? ?? ?? 48 85 ?? 74 ?? F3 0F ?? ?? ?? ?? ?? ?? 48 83 C1"
fov_offset_sig = "F3 0F ?? ?? ?? ?? ?? ?? 0F 2F ?? ?? ?? ?? ?? 72 ?? F3 0F ?? ?? ?? ?? ?? ?? 48 8B"
angle_offset_sig = "F3 0F 10 B3 ?? ?? ?? ?? 48 8D ?? ?? ?? F3 44 ?? ?? ?? ?? ?? ?? ?? F3 44"
cam_distance_reset_func_sig = "F3 0F 10 05 ?? ?? ?? ?? EB ?? F3 0F 10 05 ?? ?? ?? ?? F3 0F 10 94 24 B0 00 00 00"

DEFAULT = {
    'zoom': {
        'min': 1.5,
        'max': 20,
    },
    'fov': {
        'min': 0.69,
        'max': 0.78,
    },
    'angle': {
        'min': -1.4835298,
        'max': 0.7853982,
    },
}


class MinMax(OffsetStruct({
    'min': c_float,
    'max': c_float
})):
    def set_min(self, num: float):
        write_float(addressof(self), float(num))

    def set_max(self, num: float):
        write_float(addressof(self) + 4, float(num))

    def set(self, data: dict):
        self.set_min(data['min'])
        self.set_max(data['max'])


class ZoomPlugin2(PluginBase):
    name = "Zoom2"

    def __init__(self):
        super().__init__()

        am = AddressManager(self.storage.data, self.logger)

        self.cam_ptr = am.get('cam_ptr', scan_address, cam_sig, cmd_len=7)
        self.cam_collision_jmp_addr = am.get('cam_collision_jmp', scan_pattern, cam_collision_jmp_sig)
        zoom_offset = read_int(am.get('zoom_offset_addr', scan_pattern, zoom_offset_sig, add=4))
        fov_offset = read_int(am.get('fov_offset_addr', scan_pattern, fov_offset_sig, add=4))
        angle_offset = read_int(am.get('angle_offset_addr', scan_pattern, angle_offset_sig, add=4))
        self.cam_distance_reset_addr = am.get('cam_distance_reset', scan_pattern, cam_distance_reset_func_sig)

        version_data = self.storage.data[FFxiv_Version]
        if 'cam_distance_reset_original' not in version_data:
            version_data['cam_distance_reset_original'] = base64.b64encode(read_ubytes(self.cam_distance_reset_addr, 8)).decode('ascii')
        self.cam_distance_reset_original = base64.b64decode(version_data['cam_distance_reset_original'].encode('ascii'))

        self.storage.data.setdefault('user_default', DEFAULT)
        self.storage.data.setdefault('user_default_no_collision', False)

        self.storage.save()

        self.cam = read_memory(PointerStruct(OffsetStruct({
            'zoom': (MinMax, zoom_offset + 4),
            'fov': (MinMax, fov_offset + 4),
            'angle': (MinMax, angle_offset),
        }), 0), self.cam_ptr).value
        api.command.register(command, self.process_command)

    def reset_default(self):
        self.storage.data['user_default'] = DEFAULT
        self.storage.data['user_default_no_collision'] = False
        self.storage.save()

    def apply_default(self):
        self.set_cam(self.storage.data['user_default'])
        self.set_cam_no_collision(self.storage.data['user_default_no_collision'])
        self.set_cam_distance_no_reset(True)

    def _start(self):
        self.apply_default()

    def _onunload(self):
        api.command.unregister(command)
        self.set_cam_distance_no_reset(False)
        self.set_cam_no_collision(False)
        self.set_cam(DEFAULT)

    def set_cam(self, data: dict):
        self.cam.zoom.set(data['zoom'])
        self.cam.fov.set(data['fov'])
        self.cam.angle.set(data['angle'])

    def set_cam_distance_no_reset(self, mode: bool):
        write_ubytes(self.cam_distance_reset_addr, bytearray(b'\x90' * 8 if mode else self.cam_distance_reset_original))

    def get_cam_distance_no_reset(self):
        return read_ubytes(self.cam_distance_reset_addr, 8) == bytearray(b'\x90' * 8)

    def set_cam_no_collision(self, mode: bool):
        write_ubytes(self.cam_collision_jmp_addr, bytearray(b'\x90\xe9' if mode else b'\x0F\x84'))

    def get_cam_no_collision(self):
        return read_ubytes(self.cam_collision_jmp_addr, 2) == bytearray(b'\x90\xe9')

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))
        self.storage.save()

    def _process_min_max(self, args):
        if len(args) < 3:
            raise Exception("args is too short")
        new_num = float(args[2])

        if args[0] == 'zoom':
            mem_target = self.cam.zoom
            d_target = self.storage.data['user_default']['zoom']
        elif args[0] == 'fov':
            mem_target = self.cam.fov
            d_target = self.storage.data['user_default']['fov']
        elif args[0] == 'angle':
            mem_target = self.cam.angle
            d_target = self.storage.data['user_default']['angle']
        else:
            raise Exception("unknown arg [%s]" % args[0])

        if args[1] == 'min':
            original = mem_target.min
            mem_target.set_min(new_num)
            d_target['min'] = new_num
        elif args[1] == 'max':
            original = mem_target.max
            mem_target.set_max(new_num)
            d_target['max'] = new_num
        else:
            raise Exception("unknown arg [%s]" % args[1])

        return original, new_num

    def _process_command(self, arg):
        try:
            if not arg:
                return "/e {cmd} [zoom/fov/angle] *[min/max] *[num]\n" \
                       "/e {cmd} noCollision *[on/off]\n" \
                       "/e {cmd} [apply/reset]".format(cmd=command)
            if arg[0] in ["zoom", "fov", "angle"]:
                if len(arg) < 2:
                    mem_t = getattr(self.cam, arg[0])
                    return "%s [%s / %s]" % (arg[0], mem_t.min, mem_t.max)
                original, new_num = self._process_min_max(arg)
                return "%s %s [%s] 》 [%s]" % (arg[0], arg[1], original, new_num)
            elif arg[0] == "noCollision":
                if len(arg) < 2:
                    return "no collision mode: [%s]" % self.get_cam_no_collision()
                original = self.get_cam_no_collision()
                if arg[1] == 'on':
                    self.set_cam_no_collision(True)
                    self.storage.data['user_default_no_collision'] = True
                elif arg[1] == 'off':
                    self.set_cam_no_collision(False)
                    self.storage.data['user_default_no_collision'] = False
                else:
                    return 'unknown arg [%s]' % arg[1]
                return "no collision mode: [%s]》[%s]" % (original, self.get_cam_no_collision())

            elif arg[0] == "apply":
                self.apply_default()
                return "apply complete"

            elif arg[0] == "reset":
                self.reset_default()
                self.apply_default()
                return "reset complete"
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            self.logger.warning(traceback.format_exc())
            return str(e)
