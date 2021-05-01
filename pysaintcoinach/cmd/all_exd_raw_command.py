from pathlib import Path
import logging
from tqdm import tqdm

from . import IXivShellCommandMixin
from ..exdhelper import ExdHelper


logger = logging.getLogger('xivshell')


class AllExdRawCommand(IXivShellCommandMixin):

    def do_allrawexd(self, args):
        """
        Export all data (default), or only specific data files, separated by spaces;
        including all languages. No post-processing is applied to values.
        """

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--use-definition-version',
                            dest='use_definition_version',
                            action='store_true', default=False)
        parser.add_argument(dest='sheets', nargs='*')

        parsed_args = parser.parse_args(args.split())

        version_path = self._realm.game_version
        if parsed_args.use_definition_version:
            version_path = self._realm.definition_version

        CSV_FILE_FORMAT = "raw-exd-all/{0}{1}.csv"

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
                for lang in sheet.header.available_languages:
                    code = lang.get_code()
                    if len(code) > 0:
                        code = "." + code
                    target = Path(version_path, CSV_FILE_FORMAT.format(name, code))
                    try:
                        if not target.parent.exists():
                            target.parent.mkdir(parents=True)

                        ExdHelper.save_as_csv(sheet, lang, str(target.absolute()), True)

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
