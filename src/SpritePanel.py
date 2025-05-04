from functools import reduce
from os import listdir, path
from typing import Callable, List, Tuple
from .utility import *
from .SurfaceRect import SurfaceRect
from .ImageCache import ImageCache
from .Sprite import Sprite
from .Logger import Logger

class SpritePanel(SurfaceRect):
    # ANCHOR - SpritePanel
    
    def __init__(
        self,
        x: int,y: int, width: int, height: int,
        screen: Surface,
        sprite_dir: str,
        fill_color: Color,
        padding: int,
        scroll_speed: int
    ) -> None:
        super().__init__(x, y, width, height, screen)
        
        self.fill_color: Color = fill_color
        self.padding: int = padding
        self.scroll_speed: int = scroll_speed
        
        self.scrolling_speed_multiplier: Coords = [1, 1] # upwards and downwards
        self.is_scrolling: bool = False
        self.scroll_offset: int = 0
        
        self.canvas: Surface = Surface(self.rect.size)
        
        self.sprite_dir: str = sprite_dir
        self.sprites: Tuple[Sprite, ...] = []
        self.previous_sprite_y_pos: int = self.padding
        self.load_sprites()
        
        self.is_hovered = False
        
        self.selected_sprite_id = None
        if len(self.sprites):
            self.selected_sprite_id: str = self.sprites[0].get_id()
            self.sprites[0].select()
    
    def resize_canvas(self, amount: Coords) -> Surface:
        new_canvas: Surface = Surface((
            self.canvas.get_rect().width + amount[0],
            self.canvas.get_rect().height + amount[1]
        ), pygame.SRCALPHA)
        new_canvas.blit(self.canvas, (0, 0))
        return new_canvas
    
    def add_sprite(self, sprite_surface: Surface, sprite_name: str) -> None:
        sprite: Sprite = None
        required_space = sprite_surface.get_height() + self.padding
        if self.previous_sprite_y_pos + required_space > self.canvas.get_rect().height:
            required_total_height = self.previous_sprite_y_pos + required_space
            resize_amount = required_total_height - self.canvas.get_rect().height
            self.canvas = self.resize_canvas([0, resize_amount])

        sprite = Sprite(
            (self.canvas.get_width() - sprite_surface.get_width()) // 2,
            self.previous_sprite_y_pos,
            self.canvas,
            sprite_surface,
            sprite_name
        )
            
        self.sprites.append(sprite)

    def load_sprites(self) -> None:
        if self.sprite_dir and path.isdir(self.sprite_dir):
            try:
                sprite_files = [f for f in listdir(self.sprite_dir) if f.lower().endswith(".png")]
                for filename in sprite_files:
                    filepath = path.join(self.sprite_dir, path.basename(filename))
                    try:
                        sprite_surface: Surface = ImageCache().get_image(filename)
                        if sprite_surface.get_width() > self.rect.width:
                            aspect_ratio = sprite_surface.get_height() / sprite_surface.get_width()
                            scaled_size = [self.rect.width, int(self.rect.width * aspect_ratio)]
                            sprite_surface = ImageCache().get_image(filename, True, scaled_size)
                        self.add_sprite(sprite_surface, path.basename(filename))
                        self.previous_sprite_y_pos += sprite_surface.get_height() + self.padding
                    except pygame.error:
                        Logger.error(f"Error loading sprite: {filepath}")
                for sprite in self.sprites:
                    sprite.set_screen(self.canvas)
            except FileNotFoundError:
                Logger.error(f"Sprite directory not found: {self.sprite_dir}")

    def get_is_hovered(self, mouse_pos: Coords) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def get_sprites(self):
        return self.sprites
    
    def get_sprites_intersecting_rectangle(self, rect: Rect) -> List[Sprite]:
        return list(filter(lambda sprite: rect.colliderect(sprite.get_sprite_rect()), self.sprites))

    def get_viewport_rect(self) -> Rect:
        return Rect(
            0, -self.scroll_offset,
            *self.rect.size
        )

    def get_selected_sprite_id(self) -> str:
        return self.selected_sprite_id
    
    def has_sprite_with_name(self, name: str) -> bool:
        return name in list(map(lambda s : s.get_name(), self.sprites))
    
    def set_selected_sprite_id(self, _id: str) -> None:
        self.selected_sprite_id = _id

    # ANCHOR[id=SpritePanelUpdate]
    def _update(self, mouse_pos: Coords, event: Event, left_click_callback: Callable, right_click_callback: Callable) -> None:
        if self.get_is_hovered(mouse_pos):
            """
                If mouse cursor is at the bottom (top) fifth, then scroll down (up) faster than up (down).
                If middle then normal speed.
            """
            if abs(self.rect.bottom - mouse_pos[1]) < self.rect.height // 5:
                self.scrolling_speed_multiplier[1] = 1
                self.scrolling_speed_multiplier[0] = 2
            elif abs(self.rect.top - mouse_pos[1]) < self.rect.height // 5:
                self.scrolling_speed_multiplier[1] = 2
                self.scrolling_speed_multiplier[0] = 1
            else:
                self.scrolling_speed_multiplier[1] = 1
                self.scrolling_speed_multiplier[0] = 1
            self.is_hovered = True
            if event.type == pygame.MOUSEWHEEL:
                if event.y < 0:
                    self.scroll_offset += event.y * self.scroll_speed * self.scrolling_speed_multiplier[0]
                elif event.y > 0:
                    self.scroll_offset += event.y * self.scroll_speed * self.scrolling_speed_multiplier[1]
                
                #keep sprite_panel canvas within viewport bounds
                canvas_rect = self.canvas.get_rect()
                viewport = self.rect
                if canvas_rect.height < viewport.height:
                    self.scroll_offset = 0
                else:
                    self.scroll_offset = max(viewport.height - canvas_rect.height, min(0, self.scroll_offset))
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    left_click_callback()
                elif event.button == MouseButtons.RIGHT:
                    right_click_callback()
            
            for sprite in self.get_sprites_intersecting_rectangle(self.get_viewport_rect()):
                canvas_rect = self.canvas.get_rect(topleft=[self.rect.x, self.rect.y + self.scroll_offset])
                sprite.deselect()
                sprite.update(event, canvas_rect.topleft, self.selected_sprite_id, self.set_selected_sprite_id)
        else:
            self.is_hovered = False

    def draw_canvas(self) -> None:
        visible_canvas_rect = Rect(0, 0, *self.rect.size).clip(self.canvas.get_rect())
        canvas_offset_y = visible_canvas_rect.y - self.canvas.get_rect().y - self.scroll_offset

        self.canvas.fill(self.fill_color)
        
        for sprite in self.get_sprites_intersecting_rectangle(self.get_viewport_rect()):
            sprite.draw()
        
        self.blit(
            self.canvas,
            self.get_rect(),
            area=(0, canvas_offset_y, *self.rect.size)
        )

    # ANCHOR[id=SpritePanelDraw]
    def _draw(self) -> None:
        self.draw_canvas()