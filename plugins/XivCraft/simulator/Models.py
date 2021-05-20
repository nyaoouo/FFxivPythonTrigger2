class Recipe(object):
    detail_format = "{name}(rlv:{rlv}) - suggest: {suggest_craft}/{suggest_control} - values: {max_difficulty}/{max_quality}/{max_durability}"
    short_format = "{name}(rlv:{rlv})"

    def __init__(self, recipe_row):
        self.recipe_row = recipe_row
        self.name = recipe_row["Item{Result}"]["Name"]
        rlv_row = recipe_row["RecipeLevelTable"]
        self.rlv = rlv_row.key
        self.status_flag = rlv_row["ConditionsFlag"]
        self.suggest_craft = rlv_row["SuggestedCraftsmanship"]
        self.suggest_control = rlv_row["SuggestedControl"]
        self.max_difficulty = rlv_row["Difficulty"] * recipe_row["DifficultyFactor"] // 100
        self.max_quality = rlv_row["Quality"] * recipe_row["QualityFactor"] // 100
        self.max_durability = rlv_row["Durability"] * recipe_row["DurabilityFactor"] // 100

    def status_is_available(self, status_id):
        return bool(self.status_flag & (2 ** (status_id - 1)))

    @property
    def detail_str(self):
        return self.detail_format.format(
            name=self.name,
            rlv=self.rlv,
            suggest_craft=self.suggest_craft,
            suggest_control=self.suggest_control,
            max_difficulty=self.max_difficulty,
            max_quality=self.max_quality,
            max_durability=self.max_durability,
        )

    def __str__(self):
        return self.short_format.format(
            name=self.name,
            rlv=self.rlv,
            suggest_craft=self.suggest_craft,
            suggest_control=self.suggest_control,
            max_difficulty=self.max_difficulty,
            max_quality=self.max_quality,
            max_durability=self.max_durability,
        )


class Player(object):
    def __init__(self, lv, craft, control, max_cp):
        self.lv = lv
        self.craft = craft
        self.control = control
        self.max_cp = max_cp

    def __str__(self):
        return "({lv}) {craft}/{control}/{max_cp}".format(
            lv=self.lv, craft=self.craft, control=self.control, max_cp=self.max_cp
        )


class Skill(object):
    name = "Unknown Skill"
    pass_rounds = True
    _progress = 0
    _quality = 0
    _cost = 0
    _durability = 0

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other

    def progress(self, craft):
        return self._progress

    def quality(self, craft):
        return self._quality

    def cost(self, craft):
        return self._cost

    def durability(self, craft):
        return self._durability

    def after_use(self, craft):
        pass


class Effect(object):
    id = -1
    param: int
    name = "Unknown Effect"
    use_rounds = True
    _progress_factor = 0
    _quality_factor = 0
    _durability_factor = 0
    _cost_factor = 0

    def __str__(self):
        return "{name}({param})".format(name=self.name, param=self.param)

    def __eq__(self, other):
        return self.name == other

    def __init__(self, param=0):
        self.param = param

    def progress_factor(self, craft, used_skill):
        return self._progress_factor

    def quality_factor(self, craft, used_skill):
        return self._quality_factor

    def durability_factor(self, craft, used_skill):
        return self._durability_factor

    def cost_factor(self, craft, used_skill):
        return self._cost_factor

    def after_round(self, craft, used_skill):
        self.param -= 1
        if not self.param and self.name in craft.effects:
            del craft.effects[self.name]


class Status(object):
    id = -1
    name = "Unknown Status"
    _progress_factor = 0
    _quality_factor = 0
    _durability_factor = 0
    _cost_factor = 0

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other

    def progress_factor(self, craft, used_skill):
        return self._progress_factor

    def quality_factor(self, craft, used_skill):
        return self._quality_factor

    def durability_factor(self, craft, used_skill):
        return self._durability_factor

    def cost_factor(self, craft, used_skill):
        return self._cost_factor

    def after_round(self, craft, used_skill):
        pass
