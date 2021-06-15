from typing import Callable, Tuple, TYPE_CHECKING
from math import sin, cos

from shapely.affinity import rotate

if TYPE_CHECKING:
    from shapely.geometry import Polygon


def query(iterator, key: Callable[[any], bool], limit: int = None):
    count = 0
    for item in iterator:
        if key(item):
            count += 1
            yield item
            if limit is not None and limit <= count:
                return


def rotated_rect(cx: float, cy: float, w: float, h: float, facing_rad: float) -> 'Polygon':
    from shapely.geometry import box
    return rotate(box(cx - w / 2, cy, cx + w / 2, cy + h), -facing_rad, origin=(cx, cy), use_radians=True)


def circle(cx: float, cy: float, radius: float) -> 'Polygon':
    from shapely.geometry import Point
    return Point(cx, cy).buffer(radius)


def sector(cx: float, cy: float, radius: float, angle_rad: float, facing_rad: float, steps: int = 100) -> 'Polygon':
    from shapely.geometry import Polygon
    step_angle_width = angle_rad / steps
    segment_vertices = [(cx, cy), (cx, cy + radius)]
    segment_vertices += [(cx + sin(i * step_angle_width) * radius, cy + cos(i * step_angle_width) * radius) for i in range(1, steps)]
    return rotate(Polygon(segment_vertices), -(facing_rad - angle_rad / 2), origin=(cx, cy), use_radians=True)
