from typing import List, Dict
import json
from collections import OrderedDict

from ...datasheet import IDataRow
from ..sheet import IRelationalRow
from ..valueconverter import IValueConverter
from ..excollection import ExCollection
from .complexlinkconverter import ComplexLinkConverter
from ..definition import SheetDefinition


class ColorConverter(IValueConverter):
    @property
    def includes_alpha(self) -> bool:
        return self.__includes_alpha

    @includes_alpha.setter
    def includes_alpha(self, value):
        self.__includes_alpha = value

    @property
    def target_type_name(self):
        return 'Color'

    @property
    def target_type(self):
        return type(int)

    def __init__(self):
        self.__includes_alpha = False

    def __repr__(self):
        return "%s(IncludesAlpha=%r)" % (
            self.__class__.__name__,
            self.includes_alpha)

    def convert(self, row: IDataRow, raw_value: object):
        argb = raw_value  # type: int
        if not self.includes_alpha:
            argb = (argb | 0xFF000000)

        return argb

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'color'
        return obj

    @staticmethod
    def from_json(obj: dict):
        return ColorConverter()

    def resolve_references(self, sheet_def: SheetDefinition):
        return


class GenericReferenceConverter(IValueConverter):
    @property
    def target_type_name(self):
        return 'Row'

    @property
    def target_type(self):
        return type(IRelationalRow)

    def __repr__(self):
        return "%s()" % (self.__class__.__name__)

    def convert(self, row: IDataRow, raw_value: object):
        coll = row.sheet.collection
        key = int(raw_value)
        return coll.find_reference(key)

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'generic'
        return obj

    @staticmethod
    def from_json(obj: dict):
        return GenericReferenceConverter()

    def resolve_references(self, sheet_def: SheetDefinition):
        return


class IconConverter(IValueConverter):
    @property
    def target_type_name(self):
        return 'Image'

    @property
    def target_type(self):
        return type(object)

    def __repr__(self):
        return "%s()" % (self.__class__.__name__)

    def convert(self, row: IDataRow, raw_value: object):
        from .... import imaging
        nr = int(raw_value)
        if nr <= 0 or nr > 999999:
            return None

        sheet = row.sheet
        return imaging.IconHelper.get_icon(sheet.collection.pack_collection,
                                           nr, sheet.language)

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'icon'
        return obj

    @staticmethod
    def from_json(obj: dict):
        return IconConverter()

    def resolve_references(self, sheet_def: SheetDefinition):
        return


class MultiReferenceConverter(IValueConverter):
    @property
    def targets(self) -> List[str]: return self.__targets

    @targets.setter
    def targets(self, value): self.__targets = value

    @property
    def target_type_name(self): return 'Row'

    @property
    def target_type(self): return type(IRelationalRow)

    def __repr__(self):
        return "%s(Targets=%r)" % (
            self.__class__.__name__,
            self.targets)

    def convert(self, row: IDataRow, raw_value: object):
        key = int(raw_value)
        if self.targets is None:
            return None

        for target in self.targets:
            sheet = row.sheet.collection.get_sheet(target)
            if not any(filter(lambda r: key in r, sheet.header.data_file_ranges)):
                continue
            if key in sheet:
                return sheet[key]
        return None

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'multiref'
        obj['targets'] = self.targets or []
        return obj

    @staticmethod
    def from_json(obj: dict):
        converter = MultiReferenceConverter()
        converter.targets = [str(t) for t in obj.get('targets', [])]
        return converter

    def resolve_references(self, sheet_def: SheetDefinition):
        return


class QuadConverter(IValueConverter):
    @property
    def target_type_name(self): return 'Quad'

    @property
    def target_type(self): return type(int)

    def convert(self, row: IDataRow, raw_value: object):
        return int(raw_value)

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'quad'
        return obj

    @staticmethod
    def from_json(obj: object):
        return QuadConverter()

    def resolve_references(self, sheet_def: SheetDefinition):
        return


class SheetLinkConverter(IValueConverter):
    @property
    def target_sheet(self) -> str: return self.__target_sheet

    @target_sheet.setter
    def target_sheet(self, value): self.__target_sheet = value

    @property
    def target_type_name(self): return self.target_sheet

    @property
    def target_type(self): return type(IRelationalRow)

    def __repr__(self):
        return "%s(TargetSheet=%r)" % (
            self.__class__.__name__,
            self.target_sheet)

    def convert(self, row: IDataRow, raw_value: object):
        coll = row.sheet.collection
        if not coll.sheet_exists(self.target_sheet):
            return None

        sheet = coll.get_sheet(self.target_sheet)

        key = int(raw_value)
        return sheet[key] if key in sheet else None

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'link'
        obj['target'] = self.target_sheet
        return obj

    @staticmethod
    def from_json(obj: dict):
        converter = SheetLinkConverter()
        converter.target_sheet = obj.get('target', None)
        return converter

    def resolve_references(self, sheet_def: SheetDefinition):
        return


class TomestoneOrItemReferenceConverter(IValueConverter):
    from .... import xiv

    __tomestone_key_by_reward_index = None  # type: Dict[int, xiv.IXivRow]

    @property
    def target_type_name(self):
        return 'Item'

    @property
    def target_type(self):
        return type(IRelationalRow)

    def __repr__(self):
        return "%s()" % (self.__class__.__name__)

    def convert(self, row: IDataRow, raw_value: object):
        if self.__tomestone_key_by_reward_index is None:
            self.__tomestone_key_by_reward_index =\
                self._build_tomestone_reward_index(row.sheet.collection)

        key = int(raw_value)
        if key in self.__tomestone_key_by_reward_index:
            return self.__tomestone_key_by_reward_index[key]

        items = row.sheet.collection.get_sheet('Item')
        return items[key] if key in items else raw_value

    def _build_tomestone_reward_index(
            self, coll: ExCollection) -> Dict[int, 'xiv.IXivRow']:
        index = {}  # type: 'Dict[int, xiv.IXivRow]'

        sheet = coll.get_sheet('TomestonesItem')
        for row in sheet:
            reward_index = int(row.get_raw(2))  # For compatibility only
            if reward_index > 0:
                index[reward_index] = row['Item']

        return index

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'tomestone'
        return obj

    @staticmethod
    def from_json(obj: dict):
        return TomestoneOrItemReferenceConverter()

    def resolve_references(self, sheet_def: SheetDefinition):
        return
