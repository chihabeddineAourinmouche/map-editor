from uuid import uuid4 as u4
from typing import Callable, Optional
from .utility import *
from .ImageCache import ImageCache
from .SpriteData import SpriteData
from .Logger import Logger

class Sprite(Rect):
    selection_color: Color = None
    
    def __init__(self,
        x: int, y: int, screen: Surface,
        image: Surface,
        name: str, _id: Optional[str] = None
        
    ):
        super().__init__(x, y, image.get_width(), image.get_height())

        self.screen: Surface = screen
        
        self.image: Surface = image
        
        self.topleft: Coords = [x, y]
        
        self.name: str = name
        self.id: str = _id or str(u4())
        self.color: Color = self.selection_color
        
        self.image_cache: ImageCache = ImageCache([])
        
        self.is_selected: bool = False
        
        self.absolute_mouse_pos: Coords = pygame.mouse.get_pos()
        
        self.external_offset: Coords = [0, 0]

    # ANCHOR[id=Setters]
    def set_screen(self, screen: Surface) -> None:
        self.screen = screen
    
    def set_top_left(self, topleft: Coords):
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
            "coordinates": self.topleft
        }
    
    def get_data(self) -> SpriteData:
        return self.__dict__()
    
    def get_image(self) -> Surface:
        return self.image
    
    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_sprite_rect(self) -> Rect:
        return self
    
    def is_hovered(self) -> bool:
        offset_rect: Rect = Rect(*add_list(self.topleft, self.external_offset), *self.size)
        return offset_rect.collidepoint(self.absolute_mouse_pos)
    
    # ANCHOR[id=Update]
    def update(self,
        event: Event,
        left_click_callback: Callable,
    ) -> None:
        if self.is_hovered():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    if not self.is_selected:
                        pass
                        self.select()
                        left_click_callback(self.id)
    
    def fixed_update(self,
        offset: Coords,
        selected_id: str,
    ):
        self.absolute_mouse_pos: Coords = pygame.mouse.get_pos()
        self.external_offset = offset
        self.is_selected = self.id == selected_id
    
    def draw_selection_indicator(self):
        if self.is_selected:
                pygame.draw.rect(
                    self.screen,
                    self.color,
                    self,
                    2
                )
    
    def draw_image(self):
        offset_rect: Rect = Rect(*add_list(self.topleft, self.external_offset), *self.size)
        self.screen.blit(
            self.image,
            offset_rect
        )

    # ANCHOR[id=Update]
    def draw(self):
        self.draw_image()
        self.draw_selection_indicator()














