from pathlib import Path
import os

import pysaintcoinach
from FFxivPythonTrigger.memory import PROCESS_FILENAME
from .Logger import info

game_dir = os.environ.get('game_dir') if 'game_dir' in os.environ else Path(PROCESS_FILENAME).parent
realm = pysaintcoinach.ARealmReversed(game_dir, pysaintcoinach.ex.language.Language.chinese_simplified)
info("pysaintcoinach","realm initialized")
