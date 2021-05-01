from pathlib import Path
import logging
from tqdm import tqdm

from . import IXivShellCommandMixin
from .. import ex


logger = logging.getLogger('xivshell')


class RawSheetCommand(IXivShellCommandMixin):

    def do_rawsheet(self, args):
        """
        Export all data (default), or only specific data files, separated by spaces.
        Data is exported without any processing.
        """

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument(dest='sheets', nargs='*')

        parsed_args = parser.parse_args(args.split())

        PARTIAL_FILE_NAME_FORMAT = "exd/%s_%u%s.exd"

        if len(parsed_args.sheets) == 0:
            files_to_export = self._realm.game_data.available_sheets
        else:
            files_to_export = parsed_args.sheets

        with tqdm(files_to_export, 'sheet', unit='sheet', ncols=150,
                  bar_format='{l_bar:>50.50}{bar}{r_bar:50}') as t:
            for name in t:
                t.set_description(name)
                sheet = self._realm.game_data.get_sheet(name)

                # Get the header definition file.
                header_target = Path(self._realm.game_version, sheet.header.file.path)
                if not header_target.parent.exists():
                    header_target.parent.mkdir(parents=True)
                header_target.write_bytes(sheet.header.file.get_data())

                # Get the data file(s).
                # Unfortunately, this isn't exposed publicly, so there's a tiny bit of
                # code duplication here... Sorry...
                for _range in sheet.header.data_file_ranges:
                    data_file_name = PARTIAL_FILE_NAME_FORMAT % (
                        sheet.header.name,
                        _range.start,
                        self._realm.game_data.active_language.get_suffix())
                    data_file = sheet.collection.pack_collection.get_file(data_file_name)
                    if data_file is None:
                        data_file_name = PARTIAL_FILE_NAME_FORMAT % (
                            sheet.header.name,
                            _range.start,
                            "")
                        data_file = sheet.collection.pack_collection.get_file(data_file_name)
                        if data_file is None:
                            logger.error('Invalid data file: %s', data_file_name)
                            continue

                    data_target = Path(self._realm.game_version, data_file_name)
                    if not data_target.parent.exists():
                        data_target.parent.mkdir(parents=True)
                    data_target.write_bytes(data_file.get_data())

        print("\n")

        # Do not quit
        return False
