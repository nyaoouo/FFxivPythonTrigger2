from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from ctypes import *
from .Enum import JobClass


def byte_get_bit(byte: int, start: int, length: int):
    return (1 << length) - 1 & byte >> start


RedMageGauge = OffsetStruct({
    'white_mana': (c_ubyte, 0),
    'black_mana': (c_ubyte, 1),
})
WarriorGauge = OffsetStruct({
    'beast': (c_ubyte, 0)
})
GunbreakerGauge = OffsetStruct({
    'cartridges': (c_ubyte, 0),
    'continuationMilliseconds': (c_ushort, 2),  # Is 15000 if and only if continuationState is not zero.
    'continuationState': (c_ubyte, 4)
})
DarkKnightGauge = OffsetStruct({
    'blood': (c_ubyte, 0),
    'darksideTimer': (c_ushort, 2),
    'darkArt': (c_ubyte, 4),
    'shadowTimer': (c_ushort, 6),
})
PaladinGauge = OffsetStruct({
    'oath': (c_ubyte, 0),
})


class BardGauge(OffsetStruct({
    'songMilliseconds': (c_ushort, 0),
    'songProcs': (c_ubyte, 2),
    'soulGauge': (c_ubyte, 3),
    'songType': (c_ubyte, 4)
})):
    class Song(object):
        none = 0
        ballad = 5  # Mage's Ballad.
        paeon = 10  # Army's Paeon.
        minuet = 15  # The Wanderer's Minuet.


class DancerGauge(OffsetStruct({
    'feathers': (c_ubyte, 0),
    'esprit': (c_ubyte, 1),
    'step': (c_ubyte * 4, 2),
    'currentStep': (c_ubyte, 6)
})):
    class Step(object):
        none = 0
        emboite = 1  # red
        entrechat = 2  # blue
        jete = 3  # green
        pirouette = 4  # yellow


class DragoonGauge(OffsetStruct({
    'blood_or_life_ms': (c_ushort, 0),
    'stance': (c_ubyte, 2),  # 0 = None, 1 = Blood, 2 = Life
    'eyesAmount': (c_ubyte, 3),
})):
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
})

ThaumaturgeGauge = OffsetStruct({
    'umbralMilliseconds': (c_ushort, 2),  # Number of ms left in umbral fire/ice.
    'umbralStacks': (c_ubyte, 4),  # Positive = Umbral Fire Stacks, Negative = Umbral Ice Stacks.
})


class BlackMageGauge(OffsetStruct({
    'nextPolyglotMilliseconds': (c_ushort, 0),
    'umbralMilliseconds': (c_ushort, 2),
    'umbralStacks': (c_byte, 4),
    'umbralHearts': (c_ubyte, 5),
    'foulCount': (c_ubyte, 6),
    'enochain_state': (c_ubyte, 7),
})):
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
})

ArcanistGauge = OffsetStruct({
    'aetherflowStacks': (c_ubyte, 4),
})


class SummonerGauge(OffsetStruct({
    'stanceMilliseconds': (c_ushort, 0),
    'bahamutStance': (c_ubyte, 2),
    'bahamutSummoned': (c_ubyte, 3),
    'stacks': (c_ubyte, 4),
})):
    @property
    def aetherflowStacks(self):
        return byte_get_bit(self.stacks, 0, 2)

    @property
    def dreadwyrmStacks(self):
        return byte_get_bit(self.stacks, 2, 2)

    @property
    def phoenixReady(self):
        return byte_get_bit(self.stacks, 4, 1)


ScholarGauge = OffsetStruct({
    'aetherflowStacks': (c_ubyte, 2),
    'fairyGauge': (c_ubyte, 3),
    'fairyMilliseconds': (c_ushort, 4),  # Seraph time left ms.
    'fairyStatus': (c_ubyte, 6)
    # Varies depending on which fairy was summoned, during Seraph/Dissipation: 6 - Eos, 7 - Selene, else 0.
})

PuglistGauge = OffsetStruct({
    'lightningMilliseconds': (c_ushort, 0),
    'lightningStacks': (c_ubyte, 2),
})
MonkGauge = OffsetStruct({
    'lightningMilliseconds': (c_ushort, 0),
    'lightningStacks': (c_ubyte, 2),
    'chakraStacks': (c_ubyte, 3),
})
MachinistGauge = OffsetStruct({
    'overheatMilliseconds': (c_ushort, 0),
    'batteryMilliseconds': (c_ushort, 2),
    'heat': (c_ubyte, 4),
    'battery': (c_ubyte, 5)
})


class AstrologianGauge(OffsetStruct({
    'heldCard': (c_ubyte, 4),
    'arcanums': (c_ubyte * 3, 5),
})):
    class Card(object):
        none = 0
        balance = 1
        bole = 2
        arrow = 3
        spear = 4
        ewer = 5
        spire = 6

    class Arcanum(object):
        none = 0
        solar = 1
        lunar = 2
        celestial = 3


class SamuraiGauge(OffsetStruct({
    'kenki': (c_ubyte, 4),
    'sen_bits': (c_ubyte, 5)
})):
    @property
    def snow(self):
        return (self.sen_bits & 1) != 0

    @property
    def moon(self):
        return (self.sen_bits & 2) != 0

    @property
    def flower(self):
        return (self.sen_bits & 4) != 0


gauges = {
    JobClass.Paladin: PaladinGauge,  # 骑士PLD
    JobClass.Monk: MonkGauge,  # 武僧MNK
    JobClass.Warrior: WarriorGauge,  # 战士WAR
    JobClass.Dragoon: DragoonGauge,  # 龙骑士DRG
    JobClass.Bard: BardGauge,  # 吟游诗人BRD
    JobClass.WhiteMage: WhiteMageGauge,  # 白魔法师WHM
    JobClass.BlackMage: BlackMageGauge,  # 黑魔法师BLM
    JobClass.Arcanist: ArcanistGauge,  # 秘术师ACN
    JobClass.Summoner: SummonerGauge,  # 召唤师SMN
    JobClass.Scholar: ScholarGauge,  # 学者SCH
    JobClass.Ninja: NinjaGauge,  # 忍者NIN
    JobClass.Machinist: MachinistGauge,  # 机工士MCH
    JobClass.DarkKnight: DarkKnightGauge,  # 暗黑骑士DRK
    JobClass.Astrologian: AstrologianGauge,  # 占星术士AST
    JobClass.Samurai: SamuraiGauge,  # 武士SAM
    JobClass.RedMage: RedMageGauge,  # 赤魔法师RDM
    JobClass.Gunbreaker: GunbreakerGauge,  # 绝枪战士GNB
    JobClass.Dancer: DancerGauge,  # 舞者DNC
}
