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
    
    def is_hovered(self, offset: Coords, mouse_pos: Coords) -> bool:
        # offset should be canvas' coordinate + the panning offset + the drawing area's coordinate
        return Rect(self.rect.x + offset[0], self.rect.y + offset[1], *self.rect.size).collidepoint(mouse_pos)
    
    def update(self, event: Event) -> None:
        # Resize
        # Move
        pass

    def draw(self, surface: Surface) -> None:
        pygame.draw.rect(self.alpha_surface, self.color + list((128,)), (0, 0, self.rect.width, self.rect.height))
        # Draw diagonals
        surface.blit(self.alpha_surface, self.rect.topleft)
        pygame.draw.line(surface, self.color, (self.rect.left, self.rect.top), (self.rect.right - 1, self.rect.bottom - 1), width=1)
        pygame.draw.line(surface, self.color, (self.rect.left, self.rect.bottom - 1), (self.rect.right - 1, self.rect.top), width=1)
        pygame.draw.rect(surface, self.color, self.rect, 2)
