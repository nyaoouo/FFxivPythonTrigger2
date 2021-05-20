import logging
from pathlib import Path
from typing import cast

from . import IXivShellCommandMixin
from .. import imaging

logger = logging.getLogger('xivshell')


class UiCommand(IXivShellCommandMixin):

    UI_IMAGE_DIR_FORMAT = 'ui/icon/{0:03d}000{1}'
    UI_IMAGE_PATH_FORMAT = 'ui/icon/{0:03d}000{1}/{2:06d}.tex'
    UI_VERSIONS = [
        '',
        '/en',
        '/ja',
        '/fr',
        '/de',
        '/hq'
    ]

    def do_ui(self, args: str):
        """
        Export all, a single, or a range of UI icons.
        """

        from argparse import ArgumentParser
        from tqdm import tqdm

        parser = ArgumentParser(prog='ui')
        parser.add_argument(metavar='min', dest='v_min', type=int, nargs='?', choices=range(0, 999999), default=None)
        parser.add_argument(metavar='max', dest='v_max', type=int, nargs='?', choices=range(1, 999999), default=None)
        parsed_args = parser.parse_args(args.split())

        _min = 0
        _max = 999999

        if parsed_args.v_min is not None:
            _min = parsed_args.v_min
            if parsed_args.v_max is not None:
                _max = parsed_args.v_max
                if _max < _min:
                    logger.error('Invalid parameters.')
                    return False
            else:
                _max = _min

        count = 0

        with tqdm(self.__build_file_list(_min, _max),
                  'file', unit='file', ncols=150,
                  bar_format='{l_bar:>50.50}{bar}{r_bar:50}') as t:
            for file_path in t:
                t.set_description(file_path)
                try:
                    if self.__process(file_path):
                        count += 1
                except Exception as e:
                    logger.error('%s: %s', file_path, e)

        print("\n")
        logger.info('%d images processed', count)

        # Don't exit
        return False

    def __build_file_list(self, _min, _max):
        from ..indexfile import IndexSource
        file_list = []

        pack = self._realm.packs.get_pack('ui/')
        if isinstance(pack.source, IndexSource):
            source = cast(IndexSource, pack.source)
            # OPTIMIZATION:
            # Due to how SE organizes these files, it's possible to confirm them in groups of 1000 by
            # checking if the directory itself exists first.
            for i in range(_min, _max + 1, 1000):
                for v in self.UI_VERSIONS:
                    dir_path = self.UI_IMAGE_DIR_FORMAT.format(int(i / 1000), v)
                    if source.directory_exists(dir_path):
                        d = int(i / 1000) * 1000
                        for j in range(1000):
                            n = d + j
                            if _min <= n <= _max:
                                file_path = self.UI_IMAGE_PATH_FORMAT.format(int(n / 1000), v, n)
                                if pack.file_exists(file_path):
                                    file_list.append(file_path)
        else:
            for i in range(_min, _max):
                for v in self.UI_VERSIONS:
                    file_path = self.UI_IMAGE_PATH_FORMAT.format(int(i / 1000), v, i)
                    if pack.file_exists(file_path):
                        file_list.append(file_path)
        return file_list

    def __process(self, file_path):
        file = self._realm.packs.get_file(file_path)
        if file is not None:
            if isinstance(file, imaging.ImageFile):
                img_file = cast(imaging.ImageFile, file)
                img = img_file.get_image()

                target = Path(self._realm.game_version, file.path)
                if not target.parent.exists():
                    target.parent.mkdir(parents=True)
                png_path = target.parent.joinpath(target.stem + ".png")
                img.save(png_path)

                return True
            else:
                logger.error('%s is not an image.', file_path)
        return False
