from tqdm import tqdm
import logging
from pathlib import PurePath, Path

from . import IXivShellCommandMixin


logger = logging.getLogger('xivshell')


class BgmCommand(IXivShellCommandMixin):

    def do_bgm(self, args):
        """
        Export all BGM files.
        """

        bgms = self._realm.game_data.get_sheet('BGM')

        success_count = 0
        fail_count = 0
        with tqdm(bgms, unit='file', ncols=150,
                  bar_format='{l_bar:>50.50}{bar}{r_bar:50}') as t:
            for bgm in t:
                file_path = str(bgm['File'])

                if len(file_path) == 0:
                    continue

                try:
                    t.set_description(PurePath(file_path).stem)
                    if self.__export_file(file_path, None):
                        success_count += 1
                    else:
                        logger.error('File %s not found', file_path)
                        fail_count += 1
                except Exception:
                    logger.exception('Export of %s failed', file_path)
                    fail_count += 1

        orchestrion = self._realm.game_data.get_sheet('Orchestrion')
        orchestrion_path = self._realm.game_data.get_sheet('OrchestrionPath')
        with tqdm(orchestrion, unit='file', ncols=150,
                  bar_format='{l_bar:>50.50}{bar}{r_bar:50}') as t:
            for orchestrion_info in t:
                path = orchestrion_path[orchestrion_info.key]
                name = str(orchestrion_info['Name'])
                file_path = str(path['File'])

                if len(file_path) == 0:
                    continue

                try:
                    t.set_description(PurePath(file_path).stem)
                    if self.__export_file(file_path, name):
                        success_count += 1
                    else:
                        logger.error('File %s not found', file_path)
                        fail_count += 1
                except Exception:
                    logger.exception('Export of %s failed', file_path)
                    fail_count += 1

        print("\n")
        logger.info('%d files exported, %d failed', success_count, fail_count)

        # Do not quit
        return False

    def __export_file(self, file_path: str, suffix: str) -> bool:
        from pysaintcoinach import sound

        file = self._realm.packs.get_file(file_path)
        if file is None:
            return False

        scd_file = sound.ScdFile(file)
        count = 0
        for entry in scd_file.entries:
            if entry is None:
                continue

            base_file_name = PurePath(file_path).stem
            if suffix is not None:
                base_file_name += '-' + suffix
            count += 1
            if count > 1:
                base_file_name += '-' + count

            target_path = Path(self._realm.game_version,
                               PurePath(file_path).parent)

            extension = {sound.ScdCodec.MSADPCM: '.wav',
                         sound.ScdCodec.OGG: '.ogg'}
            target_path = target_path.joinpath(
                base_file_name + extension[sound.ScdCodec(entry.header.codec)])

            if not target_path.parent.exists():
                target_path.parent.mkdir(parents=True)

            target_path.write_bytes(entry.get_decoded())

        return True
