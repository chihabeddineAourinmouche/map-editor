from .utility import *

class SurfaceRect(Surface):
    
    def __init__(self, x: int, y: int, width: int, height: int, screen: Surface):
        super().__init__((width, height), pygame.SRCALPHA)
        
        self.rect: Rect = Rect(x, y, width, height)
        
        self.screen: Surface = screen
    
    def update(self, *args, **kwargs):
        mouse_pos: Coords = pygame.mouse.get_pos()
        self._update(mouse_pos, *args, **kwargs)
    
    def _update(self, mouse_pos: Coords, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement _update")
    
    def draw(self, *args, **kwargs):
        self._draw(*args, **kwargs)
        self.screen.blit(self, self.rect.topleft)
    
    def _draw(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement _draw")
    
    def get_relative_mouse_pos(self, mouse_pos: Coords) -> Coords:
        return [mouse_pos[0] - self.rect.topleft[0], mouse_pos[1] - self.rect.topleft[1]]
    
