import logging
from pathlib import Path

from . import IXivShellCommandMixin


logger = logging.getLogger('xivshell')


class RawCommand(IXivShellCommandMixin):

    def do_raw(self, args: str):
        """
        Save raw contents of a file.
        """

        if args is None or len(args.strip()) == 0:
            return False

        file = self._realm.packs.get_file(args.strip())
        if file is not None:
            target = Path(self._realm.game_version, file.path)
            if not target.parent.exists():
                target.parent.mkdir(parents=True)

            data = file.get_data()
            target.write_bytes(data)
        else:
            logger.error('File not found.')

        # Do not quit.
        return False
