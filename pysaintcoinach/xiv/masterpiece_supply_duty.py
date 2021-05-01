from ..ex.relational import IRelationalRow
from . import xivrow, XivRow, IXivSheet, IXivRow
from typing import List, Iterable


@xivrow
class MasterpieceSupplyDuty(XivRow):
    class CollectableItem(object):
        @property
        def masterpiece_supply_duty(self) -> 'MasterpieceSupplyDuty':
            return self.__masterpiece_supply_duty

        @property
        def required_item(self) -> 'Item':
            return self.__required_item

        @property
        def quantity(self) -> int:
            return self.__quantity

        @property
        def collectability_high_bonus(self) -> int:
            return self.__collectability_high_bonus

        @property
        def collectability_bonus(self) -> int:
            return self.__collectability_bonus

        @property
        def collectability_base(self) -> int:
            return self.__collectability_base

        @property
        def stars(self) -> int:
            return self.__stars

        @property
        def scrip_rewards(self) -> int:
            return self.__scrip_rewards

        @property
        def max_class_job_level(self) -> int:
            return self.__max_class_job_level

        @property
        def exp_modifier(self) -> int:
            return self.__exp_modifier

        def __init__(self,
                     duty: 'MasterpieceSupplyDuty',
                     index: int):
            from .item import Item

            self.__masterpiece_supply_duty = duty
            self.__required_item = duty.as_T(Item, 'RequiredItem', index)
            self.__quantity = duty.as_int32('Quantity', index)
            self.__collectability_high_bonus = duty.as_int32('Collectability{HighBonus}', index)
            self.__collectability_bonus = duty.as_int32('Collectability{Bonus}', index)
            self.__collectability_base = duty.as_int32('Collectability{Base}', index)
            self.__exp_modifier = duty.as_int32('ExpModifier', index)
            self.__scrip_rewards = duty.as_int32('Reward{Scrips}', index)
            self.__max_class_job_level = duty.as_int32('ClassJobLevel{Max}', index)
            self.__stars = duty.as_int32('Stars', index)

            bonus_multiplier_row = duty.as_T(XivRow, 'BonusMultiplier', index)
            self.__xp_multiplier = bonus_multiplier_row.as_int16('XpMultiplier', 1) / 1000
            self.__xp_multiplier2 = bonus_multiplier_row.as_int16('XpMultiplier', 0) / 1000
            self.__currency_multiplier = bonus_multiplier_row.as_int16('CurrencyMultiplier', 1) / 1000
            self.__currency_multiplier2 = bonus_multiplier_row.as_int16('CurrencyMultiplier', 0) / 1000

        def calculate_exp(self, level: int):
            # Constrain level by valid range for this collectable.
            level = min(self.masterpiece_supply_duty.class_job_level, level)
            level = max(self.max_class_job_level, level)

            # Find the base XP.
            param_grow = self.masterpiece_supply_duty.sheet.collection.get_sheet('ParamGrow')[level]
            exp_portion = 1000 / self.exp_modifier
            base_exp = param_grow.exp_to_next / exp_portion

            # Apply bonus multipliers
            return base_exp, base_exp * self.__xp_multiplier, base_exp * self.__xp_multiplier2

        def calculate_scrip_rewards(self):
            return (self.scrip_rewards,
                    self.scrip_rewards * self.__currency_multiplier,
                    self.scrip_rewards * self.__currency_multiplier2)

    @property
    def class_job(self) -> 'ClassJob':
        from .class_job import ClassJob
        return self.as_T(ClassJob)

    @property
    def class_job_level(self) -> int:
        return self.as_int32('ClassJobLevel')

    @property
    def collectable_items(self) -> 'Iterable[MasterpieceSupplyDuty.CollectableItem]':
        if self.__collectable_items is None:
            self.__collectable_items = self.__build_collectable_items()
        return self.__collectable_items

    def __init__(self, sheet: IXivSheet, source_row: IRelationalRow):
        super(MasterpieceSupplyDuty, self).__init__(sheet, source_row)
        self.__collectable_items = None  # type: List[MasterpieceSupplyDuty.CollectableItem]

    def __build_collectable_items(self):
        COUNT = 8

        return [MasterpieceSupplyDuty.CollectableItem(self, i) for i in range(COUNT)]
