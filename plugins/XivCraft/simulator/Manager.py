from inspect import isclass
from typing import Type

from .Models import *
from . import Skill as mSkill, Status as mStatus, Effects as mEffects

skills: dict[str, Type[Skill]] = dict()
effects: dict[str, Type[Effect]] = dict()
effects_id: dict[int, Type[Effect]] = dict()
status: dict[str, Type[Status]] = dict()
status_id: dict[int, Type[Status]] = dict()

for attr_name in dir(mSkill):
    attr = getattr(mSkill, attr_name)
    if isclass(attr) and issubclass(attr, Skill) and attr != Skill:
        skills[attr.name] = attr

for attr_name in dir(mStatus):
    attr = getattr(mStatus, attr_name)
    if isclass(attr) and issubclass(attr, Status) and attr != Status:
        status[attr.name] = attr
        status_id[attr.id] = attr

for attr_name in dir(mEffects):
    attr = getattr(mEffects, attr_name)
    if isclass(attr) and issubclass(attr, Effect) and attr != Effect:
        effects[attr.name] = attr
        effects_id[attr.id] = attr
