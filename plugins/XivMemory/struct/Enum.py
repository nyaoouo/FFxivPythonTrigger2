from ctypes import c_ubyte
from functools import cache

from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.memory.StructFactory import EnumStruct


class ActorType(object):
    Null = 0
    Player = 1
    BattleNpc = 2
    EventNpc = 3
    Treasure = 4
    Aetheryte = 5
    GatheringPoint = 6
    EventObj = 7
    MountType = 8
    Companion = 9  # minion
    Retainer = 10
    Area = 11
    Housing = 12
    Cutscene = 13
    CardStand = 14


job_sheet = realm.game_data.get_sheet('ClassJob')


@cache
def job_name(job_id):
    return job_sheet[job_id]['Name']


@cache
def job_short_name(job_id):
    return job_sheet[job_id]['Abbreviation']


class Jobs(EnumStruct(c_ubyte, {
    5: 'Archer',  # 弓箭手 Arc
    19: 'Paladin',  # 骑士PLD
    20: 'Monk',  # 武僧MNK
    21: 'Warrior',  # 战士WAR
    22: 'Dragoon',  # 龙骑士DRG
    23: 'Bard',  # 吟游诗人BRD
    24: 'WhiteMage',  # 白魔法师WHM
    25: 'BlackMage',  # 黑魔法师BLM
    26: 'Arcanist',  # 秘术师ACN
    27: 'Summoner',  # 召唤师SMN
    28: 'Scholar',  # 学者SCH
    30: 'Ninja',  # 忍者NIN
    31: 'Machinist',  # 机工士MCH
    32: 'DarkKnight',  # 暗黑骑士DRK
    33: 'Astrologian',  # 占星术士AST
    34: 'Samurai',  # 武士SAM
    35: 'RedMage',  # 赤魔法师RDM
    36: 'BlueMage',  # 青魔BLM
    37: 'Gunbreaker',  # 绝枪战士GNB
    38: 'Dancer',  # 舞者DNC
})):
    @property
    def name(self):
        return job_name(self.raw_value)

    @property
    def short_name(self):
        return job_short_name(self.raw_value)


class ChatType(object):
    none = 0
    Debug = 1
    Urgent = 2
    Notice = 3
    Say = 10
    Shout = 11
    TellOutgoing = 12
    TellIncoming = 13
    Party = 14
    Alliance = 15
    Linkshell1 = 16
    Linkshell2 = 17
    Linkshell3 = 18
    Linkshell4 = 19
    Linkshell5 = 20
    Linkshell6 = 21
    Linkshell7 = 22
    Linkshell8 = 23
    FreeCompany = 24
    NoviceNetwork = 27
    CustomEmote = 28
    StandardEmote = 29
    Yell = 30
    CrossParty = 32
    PvPTeam = 36
    CrossLinkShell1 = 37
    Echo = 56
    SystemError = 58
    SystemMessage = 57
    GatheringSystemMessage = 59
    ErrorMessage = 60
    RetainerSale = 71
    CrossLinkShell2 = 101
    CrossLinkShell3 = 102
    CrossLinkShell4 = 103
    CrossLinkShell5 = 104
    CrossLinkShell6 = 105
    CrossLinkShell7 = 106
    CrossLinkShell8 = 107
