from pathlib import Path
import os

import pysaintcoinach
from FFxivPythonTrigger.memory import PROCESS_FILENAME
from .Logger import info

realm = pysaintcoinach.ARealmReversed(os.environ.setdefault('game_dir',Path(PROCESS_FILENAME).parent), pysaintcoinach.ex.language.Language.chinese_simplified)
info("pysaintcoinach","realm initialized")
