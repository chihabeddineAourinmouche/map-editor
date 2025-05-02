from typing import Tuple, TypedDict
from .utility import *

class HitBoxData(TypedDict):
    id: int
    rect: Tuple[int, int, int, int]
