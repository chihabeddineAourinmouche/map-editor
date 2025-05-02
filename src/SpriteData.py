from typing import Tuple, TypedDict
from .utility import *

class SpriteData(TypedDict):
    id: int
    file_name: str
    coordinates: Tuple[int, int]
