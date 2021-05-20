from typing import cast

from .. import imaging
from ..pack import PackCollection
from ..ex.language import Language


class IconHelper(object):
    ICON_FILE_FORMAT = 'ui/icon/{0:03d}000/{1}{2:06d}.tex'

    @staticmethod
    def get_icon(pack: PackCollection,
                 nr: int,
                 language: Language = None,
                 type: str = None):
        if language is not None:
            type = language.get_code()
            if len(type) > 0:
                type += '/'
        if type is None:
            type = ''
        if len(type) > 0 and not type.endswith('/'):
            type += '/'

        file_path = IconHelper.ICON_FILE_FORMAT.format(int(nr / 1000), type, nr)

        file = pack.get_file(file_path)
        if file is None and len(type) > 0:
            # Couldn't get specific type, try for generic version.
            file_path = IconHelper.ICON_FILE_FORMAT.format(int(nr / 1000), '', nr)
            file = pack.get_file(file_path)
            if file is None:
                # Couldn't get generic version either, that's a shame :(
                pass

        return cast(imaging.ImageFile, file)
