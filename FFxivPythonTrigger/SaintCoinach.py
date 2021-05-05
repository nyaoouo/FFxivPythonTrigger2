from pathlib import Path

from .Logger import info
from FFxivPythonTrigger.memory import PROCESS_FILENAME
import pysaintcoinach

realm = pysaintcoinach.ARealmReversed(Path(PROCESS_FILENAME).parent, pysaintcoinach.ex.language.Language.chinese_simplified)
info("pysaintcoinach","realm initialized")
