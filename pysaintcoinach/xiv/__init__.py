from typing import Type

from .xivcollection import XivCollection
from .sheet import IXivRow, IXivSheet, IXivSubRow, XivRow, XivSheet, XivSubRow


REGISTERED_ROW_CLASSES = {}


def register_xivrow(cls: Type):
    REGISTERED_ROW_CLASSES[cls.__name__] = cls


def as_row_type(sheet_name: str) -> Type:
    return REGISTERED_ROW_CLASSES.get(sheet_name, XivRow)


def xivrow(cls):
    register_xivrow(cls)
    return cls


def _initialize():
    import pkgutil
    import importlib

    for importer, modname, ispkg in pkgutil.iter_modules(__path__, "."):
        importlib.import_module(modname, __package__)


_initialize()
