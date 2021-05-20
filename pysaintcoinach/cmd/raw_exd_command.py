from pathlib import Path
import logging
from tqdm import tqdm

from . import IXivShellCommandMixin
from ..exdhelper import ExdHelper
from .. import ex


logger = logging.getLogger('xivshell')


class RawExdCommand(IXivShellCommandMixin):

    def do_rawexd(self, args):
        """
        Export all data (default), or only specific data files, separated by spaces.
        No post-processing is applied to values.
        """

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument(dest='sheets', nargs='*')

        parsed_args = parser.parse_args(args.split())

        CSV_FILE_FORMAT = "rawexd/{0}.csv"

        if len(parsed_args.sheets) == 0:
            files_to_export = self._realm.game_data.available_sheets
        else:
            files_to_export = parsed_args.sheets

        success_count = 0
        fail_count = 0

        with tqdm(files_to_export, 'sheet', unit='sheet', ncols=150,
                  bar_format='{l_bar:>50.50}{bar}{r_bar:50}') as t:
            for name in t:
                t.set_description(name)
                sheet = self._realm.game_data.get_sheet(name)
                target = Path(self._realm.game_version, CSV_FILE_FORMAT.format(name))
                try:
                    if not target.parent.exists():
                        target.parent.mkdir(parents=True)

                    ExdHelper.save_as_csv(sheet, ex.Language.none, str(target.absolute()), True)

                    success_count += 1
                except Exception as e:
                    logger.exception('Export of %s failed: %s', name, e)
                    try:
                        if target.exists():
                            target.unlink()
                    except:
                        pass
                    fail_count += 1

        print("\n")
        logger.info('%d files exported, %d failed', success_count, fail_count)

        # Do not quit
        return False
