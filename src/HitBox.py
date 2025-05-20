from uuid import uuid4 as u4
from .utility import *
from .HitBoxData import HitBoxData

class HitBox:
    # ANCHOR - HitBox
    color: Color = None
    
    def __init__(self, x: int, y: int, width: int, height: int, _id: Optional[str] = None) -> None:
        self.id: str = _id or str(u4())
        self.rect: Rect = Rect(x, y, width, height)
        self.alpha_surface: Surface = Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.external_offset = [0, 0]
    
    def get_id(self) -> str:
        return self.id
    
    def __dict__(self) -> HitBoxData:
        return {
            "id": self.id,
            "rect": list(self.rect)
        }
    
    def get_data(self) -> HitBoxData:
        return self.__dict__()
    
    def get_rect(self):
        return self.rect
        
    def get_top_left(self):
        return self.rect.topleft
    
    def is_hovered(self, absolute_mouse_pos: Coords) -> bool:
        return Rect(self.rect.x + self.external_offset[0], self.rect.y + self.external_offset[1], *self.rect.size).collidepoint(absolute_mouse_pos)
    
    def update(self, external_offset: Coords) -> None:
        self.external_offset = external_offset

    def draw(self, surface: Surface) -> None:
        offset_rect: Rect = Rect(
            *add_list(self.rect.topleft, self.external_offset),
            *self.rect.size
        )
        pygame.draw.rect(self.alpha_surface, self.color + list((128,)), (0, 0, offset_rect.width, offset_rect.height))
        
        # Draw diagonals
        surface.blit(self.alpha_surface, offset_rect.topleft)
        pygame.draw.line(surface, self.color, (offset_rect.left, offset_rect.top), (offset_rect.right - 1, offset_rect.bottom - 1), width=1)
        pygame.draw.line(surface, self.color, (offset_rect.left, offset_rect.bottom - 1), (offset_rect.right - 1, offset_rect.top), width=1)
        pygame.draw.rect(surface, self.color, offset_rect, 2)
