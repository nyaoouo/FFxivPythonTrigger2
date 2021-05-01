import cmd
try:
    import readline
except ImportError:
    # This is fine... who needs bash-like support anyways, right?
    pass


from .. import ARealmReversed
# Import the supported commands.
from .all_exd_command import AllExdCommand
from .all_exd_raw_command import AllExdRawCommand
from .bgm_command import BgmCommand
from .exd_command import ExdCommand
from .image_command import ImageCommand
from .language_command import LanguageCommand
from .raw_command import RawCommand
from .raw_exd_command import RawExdCommand
from .raw_sheet_command import RawSheetCommand
from .ui_command import UiCommand


# Use mixins to add commands to the shell object.
class XivShell(cmd.Cmd,
               AllExdCommand,
               AllExdRawCommand,
               BgmCommand,
               ExdCommand,
               ImageCommand,
               LanguageCommand,
               RawCommand,
               RawExdCommand,
               RawSheetCommand,
               UiCommand):
    prompt = '(xiv) '

    def __init__(self, realm: ARealmReversed):
        super(XivShell, self).__init__()
        self._realm = realm

    def emptyline(self):
        # Do nothing if the user didn't specify a command.
        pass

    def do_exit(self, arg):
        return True
