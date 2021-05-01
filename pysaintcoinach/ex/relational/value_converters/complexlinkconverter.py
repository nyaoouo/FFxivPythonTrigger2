from abc import abstractmethod
from typing import List, cast
from collections import OrderedDict
import json

from ...sheet import IRow
from ...datasheet import IDataRow
from ..sheet import IRelationalRow, IRelationalSheet
from ..valueconverter import IValueConverter
from ..definition import SheetDefinition


class IRowProducer(object):
    @abstractmethod
    def get_row(self, sheet: IRelationalSheet, key: int) -> IRow:
        pass


class PrimaryKeyRowProducer(IRowProducer):
    def get_row(self, sheet: IRelationalSheet, key: int):
        return None if key not in sheet else sheet[key]


class IndexedRowProducer(IRowProducer):
    @property
    def key_column_name(self) -> str:
        return self.__key_column_name

    @key_column_name.setter
    def key_column_name(self, value):
        self.__key_column_name = value

    def __init__(self, key_column_name: str = None):
        self.__key_column_name = key_column_name

    def get_row(self, sheet: IRelationalSheet, key: int):
        return sheet.indexed_lookup(self.key_column_name, key)


class IProjectable(object):
    @abstractmethod
    def project(self, row: IRow) -> object:
        pass


class IdentityProjection(IProjectable):
    def project(self, row: IRow):
        return row


class ColumnProjection(IProjectable):
    @property
    def projected_column_name(self) -> str:
        return self.__projected_column_name

    @projected_column_name.setter
    def projected_column_name(self, value: str):
        self.__projected_column_name = value

    def __init__(self, projected_column_name: str):
        self.__projected_column_name = projected_column_name

    def project(self, row: IRow):
        relational_row = row  # type: IRelationalRow
        return relational_row[self.projected_column_name]


class LinkCondition(object):
    def __init__(self, **kwargs):
        self.key_column_name = kwargs.get('key_column_name', None)  # type: str
        self.key_column_index = kwargs.get('key_column_index', 0)  # type: int
        self.value = kwargs.get('value', None)  # type: object
        self.__value_type_changed = False

    def match(self, row: IDataRow) -> bool:
        row_value = row[self.key_column_index]
        if not self.__value_type_changed and row_value is not None:
            self.value = cast(type(row_value), self.value)
            self.__value_type_changed = True
        return row_value == self.value


class SheetLinkData(object):
    def __init__(self, **kwargs):
        self.projected_column_name = kwargs.get('projected_column_name', None)  # type: str
        self.key_column_name = kwargs.get('key_column_name', None)  # type: str

        self.row_producer = kwargs.get('row_producer', None)  # type: IRowProducer
        self.projection = kwargs.get('projection', None)  # type: IProjectable

        self.when = kwargs.get('when', None)  # type: LinkCondition

    @abstractmethod
    def get_row(self, key: int, collection: 'ExCollection') -> IRow:
        pass

    def to_json(self):
        obj = OrderedDict()
        if self.projected_column_name is not None:
            obj['project'] = self.projected_column_name
        if self.key_column_name is not None:
            obj['key'] = self.key_column_name
        if self.when is not None:
            obj['when'] = OrderedDict()
            obj['when']['key'] = self.when.key_column_name
            obj['when']['value'] = self.when.value

        return obj

    @staticmethod
    def from_json(obj: dict):
        data = SheetLinkData()
        if obj.get('sheet', None) is not None:
            data = SingleSheetLinkData(sheet_name=str(obj['sheet']))
        elif obj.get('sheets', None) is not None:
            data = MultiSheetLinkData(sheet_names=[str(t) for t in obj['sheets']])
        else:
            raise Exception("complexlink link must contain either 'sheet' or 'sheets'.")

        if obj.get('project', None) is None:
            data.projection = IdentityProjection()
        else:
            data.projected_column_name = str(obj['project'])
            data.projection = ColumnProjection(
                projected_column_name=data.projected_column_name)

        if obj.get('key', None) is None:
            data.row_producer = PrimaryKeyRowProducer()
        else:
            data.key_column_name = str(obj['key'])
            data.row_producer = IndexedRowProducer(
                key_column_name=data.key_column_name)

        when = obj.get('when', None)
        if when is not None:
            condition = LinkCondition()
            condition.key_column_name = str(when['key'])
            condition.value = when['value']  # Somehow convert to object?
            data.when = condition

        return data


class SingleSheetLinkData(SheetLinkData):
    def __init__(self, **kwargs):
        super(SingleSheetLinkData, self).__init__(**kwargs)
        #SheetLinkData.__init__(self, **kwargs)
        self.sheet_name = kwargs.get('sheet_name', None)  # type: str

    def to_json(self):
        obj = super(SingleSheetLinkData, self).to_json()
        obj['sheet'] = self.sheet_name
        return obj

    def get_row(self, key, collection):
        sheet = collection.get_sheet(self.sheet_name)
        return self.row_producer.get_row(sheet, key)


class MultiSheetLinkData(SheetLinkData):
    def __init__(self, **kwargs):
        super(MultiSheetLinkData, self).__init__(**kwargs)
        self.sheet_names = kwargs.get('sheet_names', None)  # type: List[str]

    def to_json(self):
        obj = super(MultiSheetLinkData, self).to_json()
        obj['sheets'] = self.sheet_names
        return obj

    def get_row(self, key, collection):
        for sheet_name in self.sheet_names:
            sheet = collection.get_sheet(sheet_name)
            if not any(filter(lambda r: key in r, sheet.header.data_file_ranges)):
                continue

            row = self.row_producer.get_row(sheet, key)
            if row is not None:
                return row
        return None


class ComplexLinkConverter(IValueConverter):
    @property
    def target_type_name(self): return 'Row'

    @property
    def target_type(self): return type(IRelationalRow)

    def __init__(self, links: 'List[SheetLinkData]'):
        self.__links = links  # type: List[SheetLinkData]

    def __repr__(self):
        return "%s()" % (self.__class__.__name__)

    def convert(self, row: IDataRow, raw_value: object):
        key = int(raw_value)
        if key == 0:
            return None
        coll = row.sheet.collection

        for link in self.__links:
            if link.when is not None and not link.when.match(row):
                continue

            result = link.get_row(key, coll)
            if result is None:
                continue

            return link.projection.project(result)

        return None

    def to_json(self):
        obj = OrderedDict()
        obj['type'] = 'complexlink'
        obj['links'] = [l.to_json() for l in self.__links]
        return obj

    @staticmethod
    def from_json(obj: dict):
        return ComplexLinkConverter(
            links=[SheetLinkData.from_json(o) for o in obj['links']])

    def resolve_references(self, sheet_def: SheetDefinition):
        for link in self.__links:
            if link.when is not None:
                key_definition = next(
                    filter(lambda d: d.inner_definition.get_name(0) == link.when.key_column_name,
                           sheet_def.data_definitions),
                    None)
                if key_definition is None:
                    raise Exception("Can't find conditional key column '%s' in sheet '%s'" %
                                    (link.when.key_column_name, sheet_def.name))

                link.when.key_column_index = key_definition.index
