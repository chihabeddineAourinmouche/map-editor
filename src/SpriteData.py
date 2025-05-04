from typing import Tuple, TypedDict
from .utility import *

class SpriteData(TypedDict):
    id: str
    file_name: str
    coordinates: Tuple[int, int]
