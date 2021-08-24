from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, EnumStruct
from ctypes import *


def byte_get_bit(byte: int, start: int, length: int):
    return (1 << length) - 1 & byte >> start


RedMageGauge = OffsetStruct({
    'white_mana': (c_ubyte, 0),
    'black_mana': (c_ubyte, 1),
}, 16)

WarriorGauge = OffsetStruct({
    'beast': (c_ubyte, 0)
}, 16)

GunbreakerGauge = OffsetStruct({
    'cartridges': (c_ubyte, 0),
    'continuationMilliseconds': (c_ushort, 2),  # Is 15000 if and only if continuationState is not zero.
    'continuationState': (c_ubyte, 4)
}, 16)

DarkKnightGauge = OffsetStruct({
    'blood': (c_ubyte, 0),
    'darksideTimer': (c_ushort, 2),
    'darkArt': (c_ubyte, 4),
    'shadowTimer': (c_ushort, 6),
}, 16)

PaladinGauge = OffsetStruct({
    'oath': (c_ubyte, 0),
}, 16)


class BardGauge(OffsetStruct({
    'songMilliseconds': (c_ushort, 0),
    'songProcs': (c_ubyte, 2),
    'soulGauge': (c_ubyte, 3),
    'songType': (EnumStruct(c_ubyte, {
        0: '',
        5: 'ballad',
        10: 'paeon',
        15: 'minuet',
    }, default=''), 4)
}, 16)):
    pass


class DancerGauge(OffsetStruct({
    'feathers': (c_ubyte, 0),
    'esprit': (c_ubyte, 1),
    'step': (EnumStruct(c_ubyte, {
        0: '',
        1: 'emboite',  # red
        2: 'entrechat',  # blue
        3: 'jete',  # green
        4: 'pirouette',  # yellow
    }) * 4, 2),
    'currentStep': (c_ubyte, 6)
}, 16)):
    pass


class DragoonGauge(OffsetStruct({
    'blood_or_life_ms': (c_ushort, 0),
    'stance': (c_ubyte, 2),  # 0 = None, 1 = Blood, 2 = Life
    'eyesAmount': (c_ubyte, 3),
}, 16)):
    @property
    def bloodMilliseconds(self):
        return self.blood_or_life_ms if self.stance == 1 else 0

    @property
    def lifeMilliseconds(self):
        return self.blood_or_life_ms if self.stance == 2 else 0


NinjaGauge = OffsetStruct({
    'hutonMilliseconds': (c_uint, 0),
    'ninkiAmount': (c_ubyte, 4),
    'hutonCount': (c_ubyte, 5),
}, 16)

ThaumaturgeGauge = OffsetStruct({
    'umbralMilliseconds': (c_ushort, 2),  # Number of ms left in umbral fire/ice.
    'umbralStacks': (c_ubyte, 4),  # Positive = Umbral Fire Stacks, Negative = Umbral Ice Stacks.
}, 16)


class BlackMageGauge(OffsetStruct({
    'nextPolyglotMilliseconds': (c_ushort, 0),
    'umbralMilliseconds': (c_ushort, 2),
    'umbralStacks': (c_byte, 4),
    'umbralHearts': (c_ubyte, 5),
    'foulCount': (c_ubyte, 6),
    'enochain_state': (c_ubyte, 7),
}, 16)):
    @property
    def enochain_active(self):
        return byte_get_bit(self.enochain_state, 0, 1)

    @property
    def polygot_active(self):
        return byte_get_bit(self.enochain_state, 1, 1)


WhiteMageGauge = OffsetStruct({
    'lilyMilliseconds': (c_ushort, 2),
    'lilyStacks': (c_ubyte, 4),
    'bloodlilyStacks': (c_ubyte, 5),
}, 16)

ArcanistGauge = OffsetStruct({
    'aetherflowStacks': (c_ubyte, 4),
}, 16)


class SummonerGauge(OffsetStruct({
    'stanceMilliseconds': (c_ushort, 0),
    'ReturnSummon': (c_ubyte, 2),
    'ReturnSummonGlam': (c_ubyte, 3),
    'stacks': (c_ubyte, 4),
}, 16)):
    @property
    def aetherflowStacks(self):
        return byte_get_bit(self.stacks, 0, 2)

    @property
    def bahamutReady(self):
        return self.stacks & 0b1000 > 0

    @property
    def phoenixReady(self):
        return self.stacks & 0b10000 > 0


ScholarGauge = OffsetStruct({
    'aetherflowStacks': (c_ubyte, 2),
    'fairyGauge': (c_ubyte, 3),
    'fairyMilliseconds': (c_ushort, 4),  # Seraph time left ms.
    'fairyStatus': (c_ubyte, 6)
    # Varies depending on which fairy was summoned, during Seraph/Dissipation: 6 - Eos, 7 - Selene, else 0.
}, 16)

PuglistGauge = OffsetStruct({
    'lightningMilliseconds': (c_ushort, 0),
    'lightningStacks': (c_ubyte, 2),
}, 16)

MonkGauge = OffsetStruct({
    'chakraStacks': (c_ushort, 0),
}, 16)

MachinistGauge = OffsetStruct({
    'overheatMilliseconds': (c_ushort, 0),
    'batteryMilliseconds': (c_ushort, 2),
    'heat': (c_ubyte, 4),
    'battery': (c_ubyte, 5)
}, 16)


class AstrologianGauge(OffsetStruct({
    'heldCard': (EnumStruct(c_ubyte, {
        0: '',
        1: 'balance',
        2: 'bole',
        3: 'arrow',
        4: 'spear',
        5: 'ewer',
        6: 'spire',
    }), 4),
    'arcanums': (EnumStruct(c_ubyte, {
        0: '',
        1: 'solar',
        2: 'lunar',
        3: 'celestial',
    }) * 3, 5),
}, 16)):
    pass


class SamuraiGauge(OffsetStruct({
    'prev_kaeshi_time': (c_ushort, 0),
    'prev_kaeshi_lv': (c_ubyte, 2),
    'kenki': (c_ubyte, 3),
    'meditation': (c_ubyte, 4),
    'sen_bits': (c_ubyte, 5)
}, 16)):
    @property
    def snow(self):
        return bool(self.sen_bits & 1)

    @property
    def moon(self):
        return bool(self.sen_bits & 2)

    @property
    def flower(self):
        return bool(self.sen_bits & 4)


gauges = {
    'Paladin': PaladinGauge,  # 骑士PLD
    'Monk': MonkGauge,  # 武僧MNK
    'Warrior': WarriorGauge,  # 战士WAR
    'Dragoon': DragoonGauge,  # 龙骑士DRG
    'Bard': BardGauge,  # 吟游诗人BRD
    'WhiteMage': WhiteMageGauge,  # 白魔法师WHM
    'BlackMage': BlackMageGauge,  # 黑魔法师BLM
    'Arcanist': ArcanistGauge,  # 秘术师ACN
    'Summoner': SummonerGauge,  # 召唤师SMN
    'Scholar': ScholarGauge,  # 学者SCH
    'Ninja': NinjaGauge,  # 忍者NIN
    'Machinist': MachinistGauge,  # 机工士MCH
    'DarkKnight': DarkKnightGauge,  # 暗黑骑士DRK
    'Astrologian': AstrologianGauge,  # 占星术士AST
    'Samurai': SamuraiGauge,  # 武士SAM
    'RedMage': RedMageGauge,  # 赤魔法师RDM
    'Gunbreaker': GunbreakerGauge,  # 绝枪战士GNB
    'Dancer': DancerGauge,  # 舞者DNC
}
