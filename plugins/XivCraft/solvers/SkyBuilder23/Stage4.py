combo = ['阔步', '改革', '观察', '注视加工', '阔步', '比尔格的祝福', '制作']


class Stage4:
    def __init__(self):
        self.queue = combo[:]

    def deal(self, craft, prev_skill=None):
        return self.queue.pop(0)

    def is_finished(self, craft, prev_skill=None):
        return not bool(self.queue)
