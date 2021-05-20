from typing import Union, Callable, TypeVar, Dict
from inspect import isfunction


TKey = TypeVar('TKey')
TValue = TypeVar('TValue')


class ConcurrentDictionary(dict, Dict[TKey, TValue]):
    def add_or_update(self,
                      key: TKey,
                      add_value: Union[TValue, Callable[[TKey], TValue]],
                      update_value_factory: Callable[[TKey, TValue], TValue]) -> TValue:
        if key not in self:
            if isfunction(add_value):
                value = self.setdefault(key, add_value(key))
            else:
                self[key] = add_value
                value = add_value
        else:
            value = update_value_factory(key, self[key])
            self[key] = value

        return value

    def get_or_add(self,
                   key: TKey,
                   value: Union[TValue, Callable[[TKey], TValue]]) -> TValue:
        if key not in self:
            if isfunction(value):
                value = self.setdefault(key, value(key))
            else:
                self[key] = value
        else:
            value = self[key]

        return value
