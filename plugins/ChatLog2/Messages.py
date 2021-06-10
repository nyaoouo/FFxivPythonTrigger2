from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.Logger import Logger
from .GetInteger import *
from .Keys import *

_logger = Logger("chat_log/messages")

world_sheet = realm.game_data.get_sheet('World')
item_sheet = realm.game_data.get_sheet('Item')
territory_type_sheet = realm.game_data.get_sheet('TerritoryType')
map_sheet = realm.game_data.get_sheet('Map')
status_sheet = realm.game_data.get_sheet('Status')
quest_sheet = realm.game_data.get_sheet('Quest')
completion_sheet = realm.game_data.get_sheet('Completion')


def extract_special_message(raw: bytearray):
    if raw.pop(0) != START_BYTE:
        raise Exception("Special Message decode, start byte mismatch")
    type_code = raw.pop(0)
    length = raw.pop(0)
    if len(raw) < length:
        raise Exception("Special Message length invalid")
    data = raw[:length]
    if data[-1] == END_BYTE: del data[-1]
    del raw[:length]
    return type_code, data


def pack_special_message(type_code: int, data: bytearray = bytearray()):
    rtn = bytearray([START_BYTE, type_code, len(data) + 1])
    rtn += data
    rtn.append(END_BYTE)
    return rtn


def extract_interactable_message(raw: bytearray):
    type_code, data = extract_special_message(raw)
    if type_code != SeStringChunkType.Interactable:
        raise Exception("this is not an interactable message")
    return data.pop(0), data


def pack_interactable_message(interact_type: int, data: bytearray = bytearray()):
    return pack_special_message(SeStringChunkType.Interactable, bytearray([interact_type]) + data)


class MessageBase(object):
    Type = "Unknown"

    def encode(self):
        return bytearray()

    def encode_group(self):
        return self.encode()

    @classmethod
    def from_buffer(cls, raw: bytearray):
        return cls()

    def text(self):
        return ''

    def __str__(self):
        return "<%s:%s>" % (self.Type, self.text())


class UnknownMessage(MessageBase):
    Type = "UnknownMessage"

    def __init__(self, raw_data: bytearray):
        self.raw_data = raw_data

    def encode(self):
        return self.raw_data

    @classmethod
    def from_buffer(cls, raw: bytearray):
        ans = cls(raw.copy())
        return raw.clear()

    def text(self):
        return self.raw_data.hex()


class TextMessage(MessageBase):
    Type = "Text"

    def __init__(self, text: str):
        self._text = text

    def encode(self):
        return self._text.encode('utf-8')

    def text(self):
        return self._text

    @classmethod
    def from_buffer(cls, raw: bytearray):
        try:
            next_idx = raw.index(START_BYTE)
        except ValueError:
            next_idx = len(raw)
        try:
            split_idx = raw.index(CHATLOG_SPLITTER)
        except ValueError:
            split_idx = len(raw)
        end_idx = min(next_idx, split_idx)
        ans = cls(raw[:end_idx].decode('utf-8', errors='ignore'))
        del raw[:end_idx]
        return ans


class SpecialMessage(MessageBase):
    Type = "UnknownSpecial"

    def __init__(self, type_code: int, data: bytearray):
        self.type_code = type_code
        self.data = data

    def encode(self):
        return pack_special_message(self.type_code, self.data)

    @classmethod
    def from_buffer(cls, raw: bytearray):
        return cls(*extract_special_message(raw))


class EmphasisItalic(MessageBase):
    Type = "EmphasisItalic"

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def text(self):
        return "enabled" if self.enabled else "disabled"

    def encode(self):
        pack_special_message(SeStringChunkType.EmphasisItalic, make_integer(int(self.enabled)))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        code, data = extract_special_message(raw)
        return cls(bool(get_integer(data)))


class SeHyphen(MessageBase):
    # Just a '–'
    Type = "SeHyphen"

    def text(self):
        return ''

    def encode(self):
        pack_special_message(SeStringChunkType.SeHyphen)

    @classmethod
    def from_buffer(cls, raw: bytearray):
        extract_special_message(raw)
        return cls()


class Interactable(MessageBase):
    Type = "Interactable/Unknown"

    def __init__(self, interact_type: int, data: bytearray):
        self.interact_type = interact_type
        self.data = data

    def encode(self):
        return pack_interactable_message(self.interact_type, self.data)

    @classmethod
    def from_buffer(cls, raw: bytearray):
        return cls(*extract_interactable_message(raw))

    def text(self):
        return '[%s - %s]' % (self.interact_type, self.data.hex())


class LinkTerminator(Interactable):
    Type = "Interactable/LinkTerminator"

    def __init__(self, interact_type: int = EmbeddedInfoType.LinkTerminator, data: bytearray = bytearray(b'\x01\x01\x01\xff\x01')):
        super(LinkTerminator, self).__init__(interact_type, data)

    def text(self):
        return ''


class Player(MessageBase):
    Type = "Interactable/Player"

    def __init__(self, server_id: int, player_name: str):
        self.server_id = server_id
        self.player_name = player_name

    def encode(self):
        encoded_name = self.player_name.encode('utf-8')
        return pack_interactable_message(EmbeddedInfoType.PlayerName, bytearray([
            0x01,
            *make_integer(self.server_id),
            0x01, 0xff,
            *make_integer(len(encoded_name)),
            *encoded_name
        ]))

    def encode_group(self):
        return self.encode() + TextMessage(self.player_name).encode() + LinkTerminator().encode()

    @classmethod
    def from_buffer(cls, raw: bytearray):
        _, data = extract_interactable_message(raw)
        data.pop(0)  # unk1
        server_id = get_integer(data)
        del data[:2]  # unk2,3
        name_len = get_integer(data)
        return cls(server_id, data[:name_len].decode('utf-8', errors='ignore'))

    def text(self):
        if self.server_id:
            return "%s@%s" % (self.player_name, world_sheet[self.server_id]['Name'])
        else:
            return self.player_name


HQ_SYMBOL = "\ue03c"


class Item(MessageBase):
    Type = "Interactable/Item"

    def __init__(self, item_id: int, is_hq: bool = False, display_name: str = None):
        self.item_id = item_id
        self.is_hq = is_hq
        self._display_name = display_name

    @property
    def display_name(self):
        if self._display_name is None:
            try:
                self._display_name = item_sheet[self.item_id]["Name"]
            except KeyError:
                self._display_name = "Unknown Item: %s" % self.item_id
        return self._display_name

    def encode(self):
        encoded_name = self.display_name + HQ_SYMBOL if self.is_hq else self.display_name
        return pack_interactable_message(EmbeddedInfoType.ItemLink, bytearray([
            *make_integer(self.item_id + 1000000 if self.is_hq else self.item_id),
            0x02, 0x01, 0xff,
            *make_integer(len(encoded_name)),
            *encoded_name
        ]))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        _, data = extract_interactable_message(raw)
        item_id = get_integer(data)
        is_hq = item_id > 1000000
        if is_hq:
            item_id -= 1000000
        if len(data) > 3:
            del data[:3]
            name_len = get_integer(data)
            display_name = data[:name_len].decode('utf-8', errors='ignore').rstrip(HQ_SYMBOL)
        else:
            display_name = None
        return cls(item_id, is_hq, display_name)

    def text(self):
        msg = "[%s]%s" % (self.item_id, self.display_name)
        if self.is_hq: msg += "(hq)"
        return msg


#
# def raw_to_in_game_coord(pos, scale):
#     c = scale / 100
#     scaled_pos = pos * c / 1000
#     return 41 / c * (scaled_pos + 1024) / 2048 + 1.0
#
#
# def in_game_to_raw_coord(pos, scale):
#     c = scale / 100
#     return int(((pos - 1) * c / 41 * 2048 - 1024) / c * 1000)


class MapPositionLink(MessageBase):
    Type = "Interactable/MapPositionLink"

    def __init__(self, territory_type_id, map_id, raw_x, raw_y):
        self.territory_type_id = territory_type_id
        self.map_id = map_id
        self.raw_x = raw_x
        self.raw_y = raw_y

    @property
    def territory_type(self):
        return territory_type_sheet[self.territory_type_id]

    @property
    def map(self):
        return map_sheet[self.map_id]

    def encode(self):
        return pack_interactable_message(EmbeddedInfoType.MapPositionLink, bytearray([
            *make_packed_integer(self.territory_type_id, self.map_id),
            *make_integer(self.raw_x),
            *make_integer(self.raw_y),
            0xff, 0x01
        ]))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        _, data = extract_interactable_message(raw)
        territory_type_id, map_id = get_packed_integer(data)
        raw_x = get_integer(data)
        raw_y = get_integer(data)
        return cls(territory_type_id, map_id, raw_x, raw_y)

    def text(self):
        return "[%s/%s](%s,%s)" % (self.territory_type['PlaceName'], self.map['PlaceName'], self.raw_x, self.raw_y)


class Status(MessageBase):
    Type = "Interactable/Status"

    def __init__(self, status_id):
        self.status_id = status_id

    def encode(self):
        return pack_interactable_message(EmbeddedInfoType.Status, bytearray([
            *make_integer(self.status_id),
            0x01, 0x01, 0xFF, 0x02, 0x20
        ]))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        _, data = extract_interactable_message(raw)
        return cls(get_integer(data))

    def text(self):
        return status_sheet[self.status_id]["Name"]


class QuestLink(MessageBase):
    Type = "Interactable/"

    def __init__(self, quest_id):
        self.quest_id = quest_id

    def encode(self):
        return pack_interactable_message(EmbeddedInfoType.QuestLink, bytearray([
            *make_integer(self.quest_id - 65536),
            0x1, 0x1,
        ]))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        _, data = extract_interactable_message(raw)
        return cls(get_integer(data) + 65536)

    def text(self):
        return quest_sheet[self.quest_id]["Name"]


class AutoTranslateKey(MessageBase):
    Type = "AutoTranslateKey"

    def __init__(self, group, key):
        self.group = group
        self.key = key

    def get_text(self):
        try:
            return completion_sheet[self.key]["Text"]
        except KeyError:
            pass
        s = None
        for r in completion_sheet:
            if r["Group"] == self.group:
                s = r["LookupTable"].split("[", 1)[0]
                break
        if s is None:
            raise KeyError("[%s] is not a valid group key" % self.group)
        try:
            return realm.game_data.get_sheet(s)[self.key]["Name"]
        except KeyError:
            return f"Unknown Data [{s}/{self.key}]"

    def encode(self):
        return pack_special_message(SeStringChunkType.AutoTranslateKey, bytearray([
            self.group,
            make_integer(self.key)
        ]))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        _, data = extract_special_message(raw)
        return cls(data.pop(0), get_integer(data))

    def text(self):
        return self.get_text()


class UIForeground(MessageBase):
    Type = "UIForeground"

    def __init__(self, color):
        self.color = color

    def encode(self):
        return pack_special_message(SeStringChunkType.UIForeground, make_integer(self.color))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        return cls(get_integer(extract_special_message(raw)[1]))

    def text(self):
        return self.color


class UIGlow(MessageBase):
    Type = "UIGlow"

    def __init__(self, color):
        self.color = color

    def encode(self):
        return pack_special_message(SeStringChunkType.UIGlow, make_integer(self.color))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        return cls(get_integer(extract_special_message(raw)[1]))

    def text(self):
        return self.color


class Icon(MessageBase):
    Type = "Icon"

    def __init__(self, icon_id):
        self.icon_id = icon_id

    def encode(self):
        return pack_special_message(SeStringChunkType.Icon, make_integer(self.icon_id))

    @classmethod
    def from_buffer(cls, raw: bytearray):
        return cls(get_integer(extract_special_message(raw)[1]))

    def text(self):
        return self.icon_id
