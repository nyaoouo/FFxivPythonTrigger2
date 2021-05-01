from pathlib import Path
from clr import AddReference
from FFxivPythonTrigger.memory import PROCESS_FILENAME
from FFxivPythonTrigger.Logger import Logger

_logger = Logger("Lumina")

res = Path(__file__).parent / 'res' / 'Lumina'
AddReference(str(res))

from Lumina import Lumina
from Lumina.Data import Language

lumina = Lumina(str(Path(PROCESS_FILENAME).parent / "sqpack"))
lumina.Options.DefaultExcelLanguage = Language.ChineseSimplified

_logger.info("lumina initialized")
