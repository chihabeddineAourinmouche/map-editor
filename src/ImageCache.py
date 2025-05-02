from os import listdir, path
from typing import List, Optional, Tuple
from .utility import *
from .Logger import Logger

class ImageCache:
    _instance = None
    _loaded = False
    _images = {}
    _scaled_images = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, image_dirs: List[str] = []):
        if not ImageCache._loaded:
            self._load_images(image_dirs)
            ImageCache._loaded = True

    def _load_images(self, image_dirs: List[str] = []) -> None:
        for image_dir in image_dirs:
            if path.isdir(image_dir):
                try:
                    file_names = list(filter(lambda f : f.lower().endswith(".png"), listdir(image_dir)))
                    for filename in file_names:
                        filepath = path.join(image_dir, filename)
                        try:
                            surface = pygame.image.load(filepath).convert_alpha()
                            image_name: str = path.basename(filepath)
                            ImageCache._images[path.basename(image_name)] = surface
                            Logger.success(f"Loaded image: {image_name} from {filepath}")
                        except pygame.error as e:
                            Logger.error(f"Error loading image {image_name} from {filepath}: {e}")
                except FileNotFoundError:
                    Logger.error(f"Error: Image directory not found: {image_dir}")

    def get_image(self, image_name: str, scaled: Optional[bool] = False, scale_dimensions: Optional[Coords] = []) -> Surface:
        surface = ImageCache._images.get(image_name)
        if scaled:
            scaled_image_name = f"{image_name}-scaled-{scale_dimensions[0]}-{scale_dimensions[1]}"
            if not ImageCache._scaled_images.get(scaled_image_name):
                ImageCache._scaled_images[path.basename(scaled_image_name)] = pygame.transform.scale(surface, scale_dimensions)
            surface = ImageCache._scaled_images[scaled_image_name]
        return surface
    
    def get_images(self, image_data: Tuple[Tuple[str, bool, Tuple[int, int]], ...]) -> List[Surface]:
        return list(map(lambda i : self.get_image(i[0], *i[1:] if len(i) > 1 else [False, []]), image_data))
    
