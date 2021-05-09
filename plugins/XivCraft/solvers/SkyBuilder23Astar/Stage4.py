combo = ['制作']


class Stage4:
    def __init__(self):
        self.queue = combo[:]

    def deal(self, craft, prev_skill=None):
        return self.queue.pop(0)

    def is_finished(self, craft, prev_skill=None):
        return not bool(self.queue)
