from pathlib import Path
import logging
import concurrent.futures
import threading
import contextlib
import sys

from tqdm import tqdm

from . import IXivShellCommandMixin
from ..exdhelper import ExdHelper
from .. import ex


logger = logging.getLogger('xivshell')


class DummyTqdmFile(object):
    file = None

    def __init__(self, file):
        self.file = file

    def write(self, x):
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self.file)

    def flush(self):
        return getattr(self.file, "flush", lambda: None)()


@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    except Exception as exc:
        raise exc
    finally:
        sys.stdout, sys.stderr = orig_out_err


class ExdCommand(IXivShellCommandMixin):

    def do_exd(self, args):
        """
        Export all data (default), or only specific data files, separated by spaces.
        """

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument(dest='sheets', nargs='*')
        parser.add_argument('-j', dest='jobs', type=int, default=1)

        parsed_args = parser.parse_args(args.split())

        cancel_event = threading.Event()

        if len(parsed_args.sheets) == 0:
            files_to_export = self._realm.game_data.available_sheets
        else:
            files_to_export = parsed_args.sheets

        success_count = 0
        fail_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=parsed_args.jobs) as executor:
            with std_out_err_redirect_tqdm() as orig_stdout:
                with tqdm(desc='Exporting sheets', unit='sheet', ncols=150, total=len(files_to_export),
                          bar_format='{l_bar:>50.50}{bar}{r_bar:50}',
                          file=orig_stdout) as t:
                    # We'll control progress manually, incrementing as each job completes.
                    tasks = {executor.submit(self.__export_file,
                                             file,
                                             cancel_event,
                                             orig_stdout): file for file in files_to_export}
                    try:
                        while len(tasks) > 0:
                            # Wait one second, and check if any have completed
                            done, not_done = concurrent.futures.wait(tasks, 1)
                            # Update progress.
                            t.update(len(done))
                            for task in done:
                                try:
                                    task.result()
                                except Exception:
                                    fail_count += 1
                                else:
                                    success_count += 1
                            # Move the still incomplete tasks to tasks and repeat.
                            tasks = not_done
                    except KeyboardInterrupt:
                        # Attempt to cancel all remaining tasks.
                        for task in tasks:
                            task.cancel()
                        # Let any tasks running know to cancel progress now.
                        cancel_event.set()
                        t.write('EXPORT WAS CANCELLED')

        print("\n")
        logger.info('%d files exported, %d failed', success_count, fail_count)

        # Do not quit
        return False

    def __export_file(self, filename, cancel_event, orig_stdout):
        CSV_FILE_FORMAT = "exd/{0}.csv"

        sheet = self._realm.game_data.get_sheet(filename)
        target = Path(self._realm.game_version, CSV_FILE_FORMAT.format(filename))

        # Use the thread naming conventions to assign the tracker position...
        _tname = threading.current_thread().name
        _pos = _tname.rindex('_')
        _n_pos = int(_tname[_pos+1:]) + 1
        with tqdm(unit='row', leave=False, ncols=150, position=_n_pos, file=orig_stdout,
                  total=len(sheet), desc=sheet.name,
                  bar_format='{l_bar:>50.50}{bar}{r_bar:50}') as tracker:
            try:
                if not target.parent.exists():
                    target.parent.mkdir(parents=True)

                ExdHelper.save_as_csv(sheet, ex.Language.none, str(target.absolute()), False,
                                      tracker=tracker, cancel_event=cancel_event)
            except Exception as e:
                logger.exception('Export of %s failed: %s', filename, e)
                try:
                    if target.exists():
                        target.unlink()
                except:
                    pass
                raise  # Pass the exception up
            finally:
                if cancel_event.is_set():
                    tracker.clear()
