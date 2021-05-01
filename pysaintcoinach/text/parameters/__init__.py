from typing import Dict
from copy import copy


class ParameterBase(object):
    @property
    def fallback_value(self) -> object:
        return self.__fallback_value

    @fallback_value.setter
    def fallback_value(self, value: object):
        self.__fallback_value = value

    def __init__(self):
        self.__fallback_value = None  # type: object
        self.__values = {}  # type: Dict[int, object]

    def __copy__(self):
        clone = ParameterBase()
        clone.__fallback_value = self.__fallback_value
        clone.__values = copy(self.__values)
        return clone

    def clear(self):
        self.__values.clear()

    def remove(self, index: int) -> bool:
        if index in self.__values:
            del self.__values[index]
            return True
        else:
            return False

    def __getitem__(self, item: int) -> object:
        return self.__values.get(item, self.fallback_value)

    def __setitem__(self, key: int, value: object):
        self.__values[key] = value
