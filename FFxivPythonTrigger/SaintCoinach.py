import os

import pysaintcoinach

from .Logger import info

if 'game_dir' in os.environ:
    game_dir = os.environ.get('game_dir')
else:
    from pathlib import Path
    from FFxivPythonTrigger.memory import PROCESS_FILENAME

    game_dir = Path(PROCESS_FILENAME).parent

if 'game_lang' in os.environ:
    game_dir = os.environ.get('game_lang')
else:
    from FFxivPythonTrigger import game_language

    language = pysaintcoinach.ex.language.Language(game_language)

realm = pysaintcoinach.ARealmReversed(game_dir, language)
info("pysaintcoinach", f"{game_language} realm initialized")
