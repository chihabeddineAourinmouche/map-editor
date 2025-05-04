from typing import Tuple, TypedDict
from .utility import *

class HitBoxData(TypedDict):
    id: str
    rect: Tuple[int, int, int, int]
