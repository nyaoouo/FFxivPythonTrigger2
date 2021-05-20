from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ctypes import c_ulonglong,POINTER
from .Actor import Actor

Target = OffsetStruct({
    "_current": (POINTER(Actor), 0x80),
    "_mouse_over": (POINTER(Actor), 0xD0),
    "_focus": (POINTER(Actor), 0xF8),
    "_previous": (POINTER(Actor), 0x110),
})
