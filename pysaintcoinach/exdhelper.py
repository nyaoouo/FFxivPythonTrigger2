from typing import cast, Iterable
from .ex.language import Language
import csv


class ExdHelper(object):
    from .ex import ISheet, IRow, IMultiRow
    from .ex.relational import IRelationalSheet

    @staticmethod
    def save_as_csv(sheet: IRelationalSheet,
                    language: Language,
                    path: str,
                    write_raw: bool,
                    tracker=None,
                    cancel_event=None):
        with open(path, 'w', encoding='utf8', newline='') as s:
            writer = csv.writer(s)
            index_line = ['key']
            name_line = ['#']
            type_line = ['int32']

            col_indices = []
            for col in sheet.header.columns:
                index_line.append(col.index)
                name_line.append(col.name)
                type_line.append(col.value_type)

                col_indices.append(col.index)

            writer.writerow(index_line)
            writer.writerow(name_line)
            writer.writerow(type_line)

            ExdHelper.write_rows(writer, sheet, language, col_indices, write_raw,
                                 tracker=tracker, cancel_event=cancel_event)

    @staticmethod
    def write_rows(writer,
                   sheet: ISheet,
                   language: Language,
                   col_indices: Iterable[int],
                   write_raw: bool,
                   tracker=None,
                   cancel_event=None):
        from .ex import ISheet, IRow
        from .xiv import XivRow
        from . import ex
        from .ex import variant2

        if tracker is not None:
            tracker.reset(len(sheet))
            tracker.set_description('%s%s' % (sheet.name, language.get_suffix()))
        if sheet.header.variant == 1:
            ExdHelper._write_rows_core(writer,
                                       cast(ISheet[IRow], sheet),
                                       language,
                                       col_indices, write_raw, ExdHelper.get_row_key,
                                       tracker=tracker, cancel_event=cancel_event)
        else:
            ExdHelper._write_rows_core(writer,
                                       cast(ISheet[XivRow], sheet),
                                       language,
                                       col_indices, write_raw, ExdHelper.get_sub_row_key,
                                       tracker=tracker, cancel_event=cancel_event)


    @staticmethod
    def _write_rows_core(writer,
                         rows: Iterable[IRow],
                         language: Language,
                         col_indices: Iterable[int],
                         write_raw: bool,
                         write_key,
                         tracker=None,
                         cancel_event=None):
        for row in rows:
            from .ex import ISheet, IRow, IMultiRow
            from .xiv import XivRow, IXivRow

            use_row = row

            if cancel_event is not None:
                if cancel_event.is_set():
                    return

            if isinstance(use_row, IXivRow):
                use_row = cast(IXivRow, row).source_row
            multi_row = cast(IMultiRow, use_row)

            row_line = [write_key(use_row)]
            for col in col_indices:
                if language == Language.none or multi_row is None:
                    v = use_row.get_raw(col) if write_raw else use_row[col]
                else:
                    v = multi_row.get_raw(col, language) if write_raw else multi_row[(col, language)]

                row_line.append(v)

            writer.writerow(row_line)

            if tracker is not None:
                tracker.update()

    @staticmethod
    def convert_rows(sheet: ISheet, language: Language = Language.none, cols = None):
        if cols is None:
            cols = sheet.header.columns

        if sheet.header.variant == 1:
            return ExdHelper.convert_rows_core(sheet, language, cols, ExdHelper.get_row_key)
        else:
            return ExdHelper.convert_rows_core(sheet, language, cols, ExdHelper.get_sub_row_key)

    @staticmethod
    def convert_rows_core(rows, language, cols, get_key):
        out_rows = {}
        for row in sorted(rows, key=lambda x: x.key):
            key, row_dict = ExdHelper._convert_row(row, language, cols, get_key)
            out_rows[key] = row_dict
        return out_rows

    @staticmethod
    def convert_row(row: IRow, language: Language = Language.none):
        cols = row.sheet.header.columns
        if row.sheet.header.variant == 1:
            get_key = ExdHelper.get_row_key
        else:
            get_key = ExdHelper.get_sub_row_key
        return ExdHelper._convert_row(row, language, cols, get_key)

    @staticmethod
    def _convert_row(row, language, cols, get_key):
        from .ex import ISheet, IRow, IMultiRow
        from .xiv import XivRow, IXivRow
        use_row = row

        if isinstance(use_row, IXivRow):
            use_row = row.source_row
        multi_row = cast(IMultiRow, use_row)

        key = get_key(use_row)
        out_row = {}
        for col in cols:
            v = None
            if language == Language.none or multi_row is None:
                v = use_row[col.index]
            else:
                v = multi_row[(col.index, language)]

            if v is not None:
                out_row[col.name or col.index] = str(v)

        return key, out_row

    @staticmethod
    def get_row_key(row: IRow):
        return row.key

    @staticmethod
    def get_sub_row_key(row: IRow):
        from .ex import variant2 as Variant2
        sub_row = cast(Variant2.SubRow, row)
        return sub_row.full_key
