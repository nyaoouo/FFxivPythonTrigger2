from pathlib import Path

from FFxivPythonTrigger.memory import PROCESS_FILENAME

try:
    with open(Path(PROCESS_FILENAME).parent / "ffxivgame.ver") as fi:
        FFxiv_Version = fi.read()
except FileNotFoundError:
    FFxiv_Version = None
else:
    from .FFxivPythonTrigger import *
