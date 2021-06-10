START_BYTE = 2
END_BYTE = 3
CHATLOG_SPLITTER=b"\x1f"


class SeStringChunkType(object):
    Icon = 0x12
    EmphasisItalic = 0x1A
    SeHyphen = 0x1F
    Interactable = 0x27
    AutoTranslateKey = 0x2E
    UIForeground = 0x48
    UIGlow = 0x49


class EmbeddedInfoType(object):
    PlayerName = 0x01
    ItemLink = 0x03
    MapPositionLink = 0x04
    QuestLink = 0x05
    Status = 0x09
    DalamudLink = 0x0F
    LinkTerminator = 0xCF
