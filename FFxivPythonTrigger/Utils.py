from typing import Callable


def query(iterator, key: Callable[[any], bool], limit: int = None):
    count = 0
    for item in iterator:
        if key(item):
            count += 1
            yield item
            if limit is not None and limit <= count:
                return
