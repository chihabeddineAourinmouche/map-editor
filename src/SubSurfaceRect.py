from .utility import *

class SubSurfaceRect():
    
    def __init__(self, x: int, y: int, width: int, height: int, screen: Surface):
        self.screen: Surface = screen
        
        self.rect: Rect = Rect(x, y, width, height)
        
        self.surface: Surface = self.screen.subsurface(self.rect)

    """
        Copy methods from Surface
    """
    def get_top(self, *args, **kwargs):
        return self.surface.get_top(*args, **kwargs)

    def get_left(self, *args, **kwargs):
        return self.surface.get_left(*args, **kwargs)

    def get_right(self, *args, **kwargs):
        return self.surface.get_right(*args, **kwargs)

    def get_bottom(self, *args, **kwargs):
        return self.surface.get_bottom(*args, **kwargs)

    def convert(self, *args, **kwargs):
        return self.surface.convert(*args, **kwargs)

    def convert_alpha(self, *args, **kwargs):
        return self.surface.convert_alpha(*args, **kwargs)

    def copy(self, *args, **kwargs):
        return self.surface.copy(*args, **kwargs)

    def fill(self, *args, **kwargs):
        return self.surface.fill(*args, **kwargs)

    def set_alpha(self, *args, **kwargs):
        return self.surface.set_alpha(*args, **kwargs)

    def get_size(self, *args, **kwargs):
        return self.surface.get_size(*args, **kwargs)

    def get_width(self, *args, **kwargs):
        return self.surface.get_width(*args, **kwargs)

    def get_height(self, *args, **kwargs):
        return self.surface.get_height(*args, **kwargs)

    def get_rect(self, *args, **kwargs):
        return self.surface.get_rect(*args, **kwargs)

    def blit(self, *args, **kwargs):
        return self.surface.blit(*args, **kwargs)

    
    def update(self, *args, **kwargs):
        mouse_pos: Coords = pygame.mouse.get_pos()
        self._update(mouse_pos, *args, **kwargs)
    
    def _update(self, mouse_pos: Coords, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement _update")
    
    def draw(self, *args, **kwargs):
        self._draw(*args, **kwargs)
    
    def _draw(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement _draw")
    
    def get_relative_mouse_pos(self, mouse_pos: Coords) -> Coords:
        return [mouse_pos[0] - self.rect.topleft[0], mouse_pos[1] - self.rect.topleft[1]]
