from .struct import Movement
from . import AddressManager
from FFxivPythonTrigger.memory import read_memory


movement = read_memory(Movement.Movement, AddressManager.movement_addr)
