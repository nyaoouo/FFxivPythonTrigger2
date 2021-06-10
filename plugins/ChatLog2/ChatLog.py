from functools import cached_property
from traceback import format_exc

from .Messages import *

_logger = Logger("ChatLog/ChatLog")


def get_next_message(raw: bytearray):
    if raw[0] != START_BYTE:
        return TextMessage.from_buffer(raw)
    else:
        if raw[1] == SeStringChunkType.EmphasisItalic:
            return EmphasisItalic.from_buffer(raw)
        elif raw[1] == SeStringChunkType.SeHyphen:
            return SeHyphen.from_buffer(raw)
        elif raw[1] == SeStringChunkType.Interactable:
            if raw[3] == EmbeddedInfoType.PlayerName:
                return Player.from_buffer(raw)
            elif raw[3] == EmbeddedInfoType.ItemLink:
                return Item.from_buffer(raw)
            elif raw[3] == EmbeddedInfoType.MapPositionLink:
                return MapPositionLink.from_buffer(raw)
            elif raw[3] == EmbeddedInfoType.Status:
                return Status.from_buffer(raw)
            elif raw[3] == EmbeddedInfoType.QuestLink:
                return QuestLink.from_buffer(raw)
            elif raw[3] == EmbeddedInfoType.LinkTerminator:
                return LinkTerminator.from_buffer(raw)
            else:
                return Interactable.from_buffer(raw)
        elif raw[1] == SeStringChunkType.AutoTranslateKey:
            return AutoTranslateKey.from_buffer(raw)
        elif raw[1] == SeStringChunkType.UIForeground:
            return UIForeground.from_buffer(raw)
        elif raw[1] == SeStringChunkType.UIGlow:
            return UIGlow.from_buffer(raw)
        elif raw[1] == SeStringChunkType.Icon:
            return Icon.from_buffer(raw)
        else:
            return SpecialMessage.from_buffer(raw)


def get_message_chain(raw: bytearray):
    backup = raw.hex()
    messages = []
    try:
        while raw and raw[0] != CHATLOG_SPLITTER[0]:
            msg = get_next_message(raw)
            if msg is None: raise Exception("None messages")
            messages.append(msg)
    except Exception:
        _logger.warning(f'err in getting msg chain:\n{backup}\n{format_exc()}')
        messages.append(UnknownMessage.from_buffer(raw))
    return messages


def group_message_chain(message_chain):
    messages = []
    skip = False
    for msg in message_chain:
        if skip:
            skip = msg.Type != "Interactable/LinkTerminator"
            continue
        if msg.Type.startswith("Interactable/"):
            skip = True
        if msg.Type == "UIForeground" or msg.Type == "UIGlow":
            continue
        messages.append(msg)
    return messages


def get_text_from_chain(message_chain):
    ans = ""
    for msg in message_chain:
        if isinstance(msg, TextMessage):
            ans += msg.text()
    return ans


class ChatLog(object):
    def __init__(self, timestamp: int, channel_id: int, sender: list[MessageBase], messages: list[MessageBase]):
        self.timestamp = timestamp
        self.channel_id = channel_id
        self.sender = sender
        self.messages = messages

    @cached_property
    def sender_grouped(self):
        return group_message_chain(self.sender)

    @cached_property
    def sender_text(self):
        return get_text_from_chain(self.sender)

    @cached_property
    def messages_grouped(self):
        return group_message_chain(self.messages)

    @cached_property
    def messages_text(self):
        return get_text_from_chain(self.messages)

    def __str__(self):
        s1 = "".join([str(n) for n in self.sender_grouped])
        s2 = "".join([str(n) for n in self.messages_grouped])
        return f"{s1}:{s2}"

    def encode(self):
        encoded_sender = bytearray()
        for msg in self.sender: encoded_sender += msg.encode()
        encoded_message = bytearray()
        for msg in self.messages: encoded_message += msg.encode()
        return bytearray([
            *pack('I', self.timestamp),
            *pack('I', self.channel_id),
            *CHATLOG_SPLITTER,
            *encoded_sender,
            *CHATLOG_SPLITTER,
            *encoded_message
        ])

    @classmethod
    def from_buffer(cls, raw: bytearray):
        time = int.from_bytes(raw[0:4], byteorder='little')
        channel_id = int.from_bytes(raw[4:8], byteorder='little')
        data = raw[9:]
        sender = get_message_chain(data)
        data.pop(0)  # pop split key
        messages = get_message_chain(data)
        return cls(time, channel_id, sender, messages)
