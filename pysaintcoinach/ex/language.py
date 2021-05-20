from enum import Enum


class Language(Enum):
    none = ""
    japanese = "ja"
    english = "en"
    german = "de"
    french = "fr"
    chinese_simplified = "chs"
    chinese_traditional = "cht"
    korean = "ko"
    unsupported = "?"

    def get_code(self):
        return self.value

    def get_suffix(self):
        code = self.get_code()
        if len(code) > 0:
            return "_" + code
        else:
            return ""
