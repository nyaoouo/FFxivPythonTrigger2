import logging
from pathlib import PurePath, Path
from typing import cast

from . import IXivShellCommandMixin
from .. import imaging

logger = logging.getLogger('xivshell')


class ImageCommand(IXivShellCommandMixin):

    def do_image(self, args: str):
        """
        Export an image file.
        """

        file = self._realm.packs.get_file(args.strip())
        if file is not None:
            if isinstance(file, imaging.ImageFile):
                img_file = cast(imaging.ImageFile, file)
                img = img_file.get_image()

                target = Path(self._realm.game_version, file.path)
                if not target.parent.exists():
                    target.parent.mkdir(parents=True)
                png_path = target.parent.joinpath(target.stem + ".png")
                img.save(png_path)
            else:
                logger.error('File is not an image (actual: %s).', file.common_header.file_type)
        else:
            logger.error('File not found.')

        # Do not quit
        return False
