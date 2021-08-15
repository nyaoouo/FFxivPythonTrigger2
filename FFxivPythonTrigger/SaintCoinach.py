from pathlib import Path
import os

import pysaintcoinach
from FFxivPythonTrigger import game_language
from FFxivPythonTrigger.memory import PROCESS_FILENAME
from .Logger import info

game_dir = os.environ.get('game_dir') if 'game_dir' in os.environ else Path(PROCESS_FILENAME).parent
language = pysaintcoinach.ex.language.Language(game_language)
realm = pysaintcoinach.ARealmReversed(game_dir, language)
info("pysaintcoinach", f"{game_language} realm initialized")
