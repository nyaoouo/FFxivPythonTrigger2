from .Models import Skill
import math


class BasicSynthesis(Skill):
    name = "制作"
    _durability = 10

    def progress(self, craft):
        return 120 if craft.player.lv >= 31 else 100


class BasicTouch(Skill):
    name = "加工"
    _quality = 100
    _durability = 10
    _cost = 18


class MastersMend(Skill):
    name = "精修"
    _cost = 88

    def after_use(self, craft):
        craft.current_durability = min(craft.current_durability + 30, craft.recipe.max_durability)


class HastyTouch(Skill):
    name = "仓促"
    _quality = 100
    _durability = 10


class HastyTouchFail(Skill):
    name = "仓促:fail"
    _durability = 10


class RapidSynthesis(Skill):
    name = "高速制作"
    _durability = 10

    def progress(self, craft):
        return 500 if craft.player.lv >= 63 else 250


class RapidSynthesisFail(Skill):
    name = "高速制作:fail"
    _durability = 10


class InnerQuiet(Skill):
    name = "内静"
    _cost = 18

    def after_use(self, craft):
        craft.add_effect("内静", 1)


class Observe(Skill):
    name = "观察"
    _cost = 7

    def after_use(self, craft):
        craft.add_effect("观察", 1)


class TricksOfTheTrade(Skill):
    name = "秘诀"

    def after_use(self, craft):
        craft.current_cp = min(craft.current_cp + 20, craft.player.max_cp)


class WasteNot(Skill):
    name = "俭约"
    _cost = 56

    def after_use(self, craft):
        craft.add_effect("俭约", 4)


class Veneration(Skill):
    name = "崇敬"
    _cost = 18

    def after_use(self, craft):
        craft.add_effect("崇敬", 4)


class StandardTouch(Skill):
    name = '中级加工'
    _quality = 125
    _durability = 10
    _cost = 32


class GreatStrides(Skill):
    name = '阔步'
    _cost = 32

    def after_use(self, craft):
        craft.add_effect('阔步', 3)


class Innovation(Skill):
    name = '改革'
    _cost = 18

    def after_use(self, craft):
        craft.add_effect('改革', 4)


class NameOfTheElements(Skill):
    name = '元素之美名'
    _cost = 30

    def after_use(self, craft):
        craft.add_effect('元素之美名', 3)


class BrandOfTheElements(Skill):
    name = '元素之印记'
    _cost = 6
    _progress = 100
    _durability = 10


class CarefulObservation(Skill):
    name = '最终确认'
    _cost = 1
    pass_rounds = False

    def after_use(self, craft):
        craft.add_effect('最终确认', 5)


class WasteNotTwo(Skill):
    name = '长期俭约'
    _cost = 98

    def after_use(self, craft):
        craft.add_effect("俭约", 8)


class ByregotsBlessing(Skill):
    name = '比尔格的祝福'
    _durability = 10
    _cost = 24

    def quality(self, craft):
        return 100 + (0 if "内静" not in craft.effects else craft.effects["内静"].param - 1) * 20

    def after_use(self, craft):
        if "内静" in craft.effects:
            del craft.effects["内静"]


class PreciseTouch(Skill):
    name = '集中加工'
    _quality = 150
    _durability = 10
    _cost = 18

    def after_use(self, craft):
        if "内静" in craft.effects:
            craft.effects["内静"].param = min(11, craft.effects["内静"].param + 1)


class MuscleMemory(Skill):
    name = '坚信'
    _progress = 300
    _cost = 6
    _durability = 10

    def after_use(self, craft):
        craft.add_effect('坚信', 5)


class CarefulSynthesis(Skill):
    name = '模范制作'
    _cost = 7
    _progress = 150
    _durability = 10


class PatientTouch(Skill):
    name = '专心加工'
    _cost = 6
    _quality = 100
    _durability = 10

    def after_use(self, craft):
        if "内静" in craft.effects:
            craft.effects["内静"].param = min(11, craft.effects["内静"].param * 2 - 1)


class PatientTouchFail(Skill):
    name = "专心加工:fail"
    _cost = 6
    _durability = 10

    def after_use(self, craft):
        if "内静" in craft.effects:
            craft.effects["内静"].param = math.ceil(craft.effects["内静"].param / 2)


class Manipulation(Skill):
    name = '掌握'
    _cost = 96

    def after_use(self, craft):
        craft.add_effect('掌握', 8)


class PrudentTouch(Skill):
    name = '俭约加工'
    _cost = 25
    _quality = 100
    _durability = 5


class FocusedSynthesis(Skill):
    name = '注视制作'
    _cost = 5
    _durability = 10
    _progress = 200


class FocusedTouch(Skill):
    name = '注视加工'
    _cost = 18
    _durability = 10
    _quality = 150


class FocusedSynthesisFail(Skill):
    name = "注视制作:fail"
    _cost = 5
    _durability = 10


class FocusedTouchFail(Skill):
    name = "注视加工:fail"
    _cost = 18
    _durability = 10


class Reflect(Skill):
    name = "闲静"
    _quality = 100
    _cost = 24
    _durability = 10

    def after_use(self, craft):
        craft.add_effect("内静", 3)


class PreparatoryTouch(Skill):
    name = '坯料加工'
    _quality = 200
    _cost = 40
    _durability = 20

    def after_use(self, craft):
        if "内静" in craft.effects:
            craft.effects["内静"].param = min(11, craft.effects["内静"].param + 1)


class Groundwork(Skill):
    name = "坯料制作"
    _cost = 18
    _durability = 20

    def progress(self, craft):
        return 150 if craft.current_durability < craft.get_skill_durability(self) else 300


class DelicateSynthesis(Skill):
    name = '精密制作'
    _progress = 100
    _quality = 100
    _cost = 32
    _durability = 10


class IntensiveSynthesis(Skill):
    name = '集中制作'
    _progress = 300
    _durability = 10
    _cost = 6


class TrainedEye(Skill):
    name = '工匠的神速技巧'
    _cost = 250

    def after_use(self, craft):
        craft.current_quality = craft.recipe.max_quality


class DesignChanges(Skill):
    name = '设计变动'
    pass_rounds = False
