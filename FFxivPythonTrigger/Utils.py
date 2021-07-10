from typing import Callable, Tuple, TYPE_CHECKING
from math import sin, cos
import hashlib, os

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


def dir_hash(directory_path):
    hashs = hashlib.sha256()
    if not os.path.exists(directory_path):
        return None
    for root, dirs, files in os.walk(directory_path):
        for names in files:
            filepath = os.path.join(root, names)
            with open(filepath, 'rb') as f1:
                while True:
                    buf = f1.read(4096)
                    if not buf:break
                    hashs.update(hashlib.sha256(buf).digest())
    return hashs.hexdigest()


def file_hash(file_path):
    if not os.path.exists(file_path):
        return None
    hashs = hashlib.sha256()
    with open(file_path, 'rb') as f1:
        while True:
            buf = f1.read(4096)
            if not buf: break
            hashs.update(hashlib.sha256(buf).digest())
    return hashs.hexdigest()


def get_hash(path):
    if os.path.isdir(path):
        return dir_hash(path)
    else:
        return file_hash(path)
