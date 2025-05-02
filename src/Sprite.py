from itertools import count
from typing import Callable, Optional
from .utility import *
from .ImageCache import ImageCache
from .SpriteData import SpriteData
from .Logger import Logger
from .SurfaceRect import SurfaceRect

class Sprite(SurfaceRect):
    selection_color: Color = None
    id_count = count()
    
    def __init__(self,
        x: int, y: int, screen: Surface,
        image: Surface,
        name: str, _id: Optional[int] = None
        
    ):
        super().__init__(x, y, image.get_width(), image.get_height(), screen)
        
        self.image: Surface = image
        
        self.topleft: Coords = [x, y]
        
        self.name: str = name
        self.id: int = _id or next(self.id_count)
        self.color: Color = self.selection_color
        
        self.image_cache: ImageCache = ImageCache([])
        
        self.is_selected: bool = False

    # ANCHOR[id=Setters]
    def set_screen(self, screen: Surface) -> None:
        self.screen = screen
    
    def set_top_left(self, topleft: Coords):
        self.rect.topleft = topleft
        self.topleft = topleft

    def select(self) -> None:
        self.is_selected = True
    
    def deselect(self) -> None:
        self.is_selected = False

    def set_image(self, image: Surface) -> None:
        self.image = image

    # ANCHOR[id=Getters]    
    def __dict__(self) -> SpriteData:
        return {
            "id": self.id,
            "file_name": self.name,
            "coordinates": self.rect.topleft
        }
    
    def get_data(self) -> SpriteData:
        return self.__dict__()
    
    def get_image(self) -> Surface:
        return self.image
    
    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_sprite_rect(self, topleft: Optional[Coords]=None) -> Rect:
        return self.get_rect(topleft=topleft or self.topleft)
    
    def is_hovered(self, absolute_mouse_pos: Coords, offset: Coords) -> bool:
        return self.get_sprite_rect(add_list(self.topleft, offset)).collidepoint(absolute_mouse_pos)
    
    # ANCHOR[id=Update]
    def _update(self,
        absolute_mouse_pos: Coords,
        event: Event,
        offset: Coords,
        selected_id: int,
        left_click_callback: Callable
    ) -> None:

        self.is_selected = self.id == selected_id
        if self.is_hovered(absolute_mouse_pos, offset):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    if not self.is_selected:
                        pass
                        self.select()
                        left_click_callback(self.id)
    
    def draw_selection_indicator(self):
        if self.is_selected:
                pygame.draw.rect(
                    self.screen,
                    self.color,
                    self.rect,
                    2
                )
    
    def draw_image(self):
        self.blit(
            self.image,
            (0, 0)
        )

    # ANCHOR[id=Update]
    def _draw(self):
        self.draw_image()
        self.draw_selection_indicator()














