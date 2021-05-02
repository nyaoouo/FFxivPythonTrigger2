from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ctypes import c_float

Movement = OffsetStruct({
    "speed": (c_float, 68)
})
