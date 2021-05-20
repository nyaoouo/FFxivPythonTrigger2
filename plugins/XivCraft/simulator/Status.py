from .Models import Status


class White(Status):
    id = 1
    name = "通常"


class Red(Status):
    id = 2
    name = "高品质"
    _quality_factor = 0.5


class Rainbow(Status):
    id = 3
    name = "最高品质"
    _quality_factor = 3


class Black(Status):
    id = 4
    name = "低品质"
    _quality_factor = -0.5


class Yellow(Status):
    id = 5
    name = "安定"


class Blue(Status):
    id = 6
    name = "结实"
    _durability_factor = -0.5


class Green(Status):
    id = 7
    name = "高效"
    _cost_factor = -0.5


class DeepBlue(Status):
    id = 8
    name = "高進捗"
    _progress_factor = 0.5


class Purple(Status):
    id = 9
    name = "長持続"

    def after_round(self, craft, used_skill):
        for e in craft.effect_to_add.values():
            if e.use_rounds:
                e.param += 2


DEFAULT_STATUS = White
