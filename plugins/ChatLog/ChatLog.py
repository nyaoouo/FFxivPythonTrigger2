from .GetInteger import get_integer, get_packed_integer, NotSupportedType
from .WorldName import get_world_name

START_BYTE = 2
END_BYTE = 3


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


class MessageBase(object):
    Type = "Unknown"

    def __init__(self, raw_data: bytes):
        self.raw_data = raw_data

    @classmethod
    def serialize(cls, data):
        return cls(data)

    @classmethod
    def parse(cls, raw: bytes):
        return MessageBase(raw), b''

    def text(self):
        return ''

    def __str__(self):
        return "<%s:%s>" % (self.Type, self.text())


class TextMessage(MessageBase):
    Type = "Text"

    def __init__(self, raw_data: bytes):
        super().__init__(raw_data)
        self.decoded = raw_data.decode('utf-8', errors='ignore')

    @classmethod
    def serialize(cls, text: str):
        return cls(text.encode('utf-8')),

    def text(self):
        return self.decoded

    @classmethod
    def parse(cls, raw: bytes):
        raw_text = bytearray()
        idx = 0
        while idx < len(raw) and raw[idx] != START_BYTE:
            raw_text.append(raw[idx])
            idx += 1
        return cls(raw_text), raw[idx:]


class SpecialMessage(MessageBase):
    Type = "UnknownSpecial"

    def __init__(self, raw_data: bytes):
        super(SpecialMessage, self).__init__(raw_data)
        self.type_code = raw_data[1]
        self.length = raw_data[2]

    @classmethod
    def parse(cls, raw: bytes):
        length = raw[2] + 3
        return cls(raw[:length]), raw[length:]

    def text(self):
        return '[%s]' % self.type_code


class EmphasisItalic(SpecialMessage):
    Type = "EmphasisItalic"

    def __init__(self, raw_data: bytes):
        super(EmphasisItalic, self).__init__(raw_data)
        self.enabled, _ = get_integer(raw_data[3:])

    def text(self):
        return "enabled" if self.enabled else "disabled"


class SeHyphen(SpecialMessage):
    # Just a '–'
    Type = "SeHyphen"

    def text(self):
        return ''


class Interactable(SpecialMessage):
    Type = "UnknownInteractable"

    def __init__(self, raw_data: bytes):
        super(Interactable, self).__init__(raw_data)
        self.sub_type = raw_data[3]

    def text(self):
        return '[%s - %s]' % (self.type_code, self.sub_type)


class Player(Interactable):
    Type = "Player"

    def __init__(self, raw_data: bytes):
        super(Player, self).__init__(raw_data)
        serverId, remain = get_integer(raw_data[5:])
        self.serverId = serverId + 1
        self.nameLen, remain = get_integer(remain[2:])
        self.playerName = remain[:self.nameLen].decode('utf-8', errors='ignore')

    def text(self):
        return "%s@%s" % (self.playerName, self.serverId)


class Item(Interactable):
    Type = "Item"

    def __init__(self, raw_data: bytes):
        super(Item, self).__init__(raw_data)
        i_id, remain = get_integer(raw_data[4:])
        self.is_hq = i_id > 1000000
        self.item_id = i_id - 1000000 if self.is_hq else i_id
        if len(remain) > 3:
            name_len, remain = get_integer(remain[3:])
            self.display_name = remain[:name_len].decode('utf-8', errors='ignore')
            if self.is_hq: self.display_name = self.display_name[:-1]
        else:
            self.display_name = ''

    def text(self):
        msg = "[%s]%s" % (self.item_id, self.display_name)
        if self.is_hq: msg += "(hq)"
        return msg


class MapPositionLink(Interactable):
    Type = "MapPositionLink"

    def __init__(self, raw_data: bytes):
        super(MapPositionLink, self).__init__(raw_data)
        self.territory_type_id = self.map_id = self.raw_x = self.raw_y = None
        try:
            self.territory_type_id, self.map_id, remain = get_packed_integer(raw_data[4:])
            self.raw_x, remain = get_integer(remain)
            self.raw_y, remain = get_integer(remain)
        except NotSupportedType:
            pass

    def text(self):
        return "[%s/%s](%s,%s)" % (self.territory_type_id, self.map_id, self.raw_x, self.raw_y)


class Status(Interactable):
    Type = "Status"

    def __init__(self, raw_data: bytes):
        super(Status, self).__init__(raw_data)
        self.status_id,_ = get_integer(raw_data[4:])

    def text(self): return self.status_id


class QuestLink(Interactable):
    Type = "QuestLink"

    def __init__(self, raw_data: bytes):
        super(QuestLink, self).__init__(raw_data)
        self.quest_id,_ = get_integer(raw_data[4:])

    def text(self): return self.quest_id


class DalamudLink(Interactable):
    Type = "DalamudLink"

    def __init__(self, raw_data: bytes):
        super(DalamudLink, self).__init__(raw_data)
        length = raw_data[4]
        self.plugin = raw_data[5:length + 5].decode('utf-8')
        self.command_id,_ = get_integer(raw_data[length + 5:])

    def text(self):
        return "%s/%s" % (self.plugin, self.command_id)


class AutoTranslateKey(SpecialMessage):
    Type = "AutoTranslateKey"

    def __init__(self, raw_data: bytes):
        super(AutoTranslateKey, self).__init__(raw_data)
        self.group = raw_data[3]
        self.key, _ = get_integer(raw_data[4:])

    def text(self):
        return "%s/%s" % (self.group, self.key)


class UIForeground(SpecialMessage):
    Type = "UIForeground"

    def __init__(self, raw_data: bytes):
        super(UIForeground, self).__init__(raw_data)
        self.color, _ = get_integer(raw_data[3:])

    def text(self):
        return self.color


class UIGlow(SpecialMessage):
    Type = "UIGlow"

    def __init__(self, raw_data: bytes):
        super(UIGlow, self).__init__(raw_data)
        self.color, _ = get_integer(raw_data[3:])

    def text(self):
        return self.color


class Icon(SpecialMessage):
    Type = "Icon"

    def __init__(self, raw_data: bytes):
        super(Icon, self).__init__(raw_data)
        print(self.raw_data.hex())
        self.icon_id, _ = get_integer(raw_data[3:])

    def text(self): return self.icon_id


class LinkTerminator(SpecialMessage):
    Type = "LinkTerminator"


def get_next_message(raw: bytes):
    if raw[0] != START_BYTE:
        return TextMessage.parse(raw)
    else:
        if raw[1] == SeStringChunkType.EmphasisItalic:
            return EmphasisItalic.parse(raw)
        elif raw[1] == SeStringChunkType.SeHyphen:
            return SeHyphen.parse(raw)
        elif raw[1] == SeStringChunkType.Interactable:
            if raw[3] == EmbeddedInfoType.PlayerName:
                return Player.parse(raw)
            elif raw[3] == EmbeddedInfoType.ItemLink:
                return Item.parse(raw)
            elif raw[3] == EmbeddedInfoType.MapPositionLink:
                return MapPositionLink.parse(raw)
            elif raw[3] == EmbeddedInfoType.Status:
                return Status.parse(raw)
            elif raw[3] == EmbeddedInfoType.QuestLink:
                return QuestLink.parse(raw)
            elif raw[3] == EmbeddedInfoType.DalamudLink:
                return DalamudLink.parse(raw)
            elif raw[3] == EmbeddedInfoType.LinkTerminator:
                return LinkTerminator.parse(raw)
            else:
                return LinkTerminator.parse(raw)
        elif raw[1] == SeStringChunkType.AutoTranslateKey:
            return AutoTranslateKey.parse(raw)
        elif raw[1] == SeStringChunkType.UIForeground:
            return UIForeground.parse(raw)
        elif raw[1] == SeStringChunkType.UIGlow:
            return UIGlow.parse(raw)
        elif raw[1] == SeStringChunkType.Icon:
            return Icon.parse(raw)
        else:
            return SpecialMessage.parse(raw)


def get_message_chain(raw: bytes):
    messages = []
    try:
        while raw:
            message, raw = get_next_message(raw)
            messages.append(message)
    except Exception:
        # traceback.print_exc()
        messages.append(MessageBase(raw))
    return messages





def group_message_chain(message_chain):
    messages = []
    skip = False
    for msg in message_chain:
        if skip:
            skip = not isinstance(msg, LinkTerminator)
            continue
        if isinstance(msg, Interactable):
            skip = True
        if isinstance(msg, UIForeground) or isinstance(msg, UIGlow):
            continue
        # if isinstance(msg, TextMessage) and \
        #         len(messages) > 1 and \
        #         isinstance(messages[-1], Icon) and \
        #         messages[-1].icon_id == 88 and \
        #         isinstance(messages[-2], Player):
        #     n1,n2=get_world_name(messages[-2].serverId)
        #     new_text = msg.text().lstrip(n2 if n2 else n1)
        #     msg = TextMessage.serialize(new_text)
        #     messages.pop()
        messages.append(msg)
    return messages


def get_text_from_chain(message_chain):
    ans = ""
    for msg in message_chain:
        if isinstance(msg, TextMessage):
            ans += msg.text()
    return ans


class ChatLog(object):
    def __init__(self, raw_data: bytes):
        self.raw_data = raw_data
        self.time = int.from_bytes(raw_data[0:4], byteorder='little')
        self.channel_id = int.from_bytes(raw_data[4:8], byteorder='little')
        sender_raw, msg_raw = raw_data[9:].split(b"\x1f", 1)
        self.sender = get_message_chain(sender_raw)
        self.messages = get_message_chain(msg_raw)
        self.grouped_messages = group_message_chain(self.messages)
        self.grouped_sender = group_message_chain(self.sender)
        self.text = get_text_from_chain(self.messages)
