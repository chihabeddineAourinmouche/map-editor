from functools import reduce
from typing import Callable, Dict, List, Optional, Union
from .utility import *
from .SurfaceRect import SurfaceRect
from .SubSurfaceRect import SubSurfaceRect
from .ImageCache import ImageCache
from .FontManager import FontManager
from .Logger import Logger
from os import path

class Display(SubSurfaceRect):
    # ANCHOR - Display

    def __init__(
        self,
        x: int, y: int, width: int, height: int, screen: Surface,
        display_icon_size: List[int],
        cursor_icon_size: int,
        display_icons: List[str],
        cursor_icons: List[str],
        font_size: int,
        font_color: Color,
        tooltip_padding: int,
        fill_color: str,
        icon_fill_color: str
    ) -> None:
        super().__init__(x, y, width, height, screen)
        
        self.font_size = font_size
        self.font_color = font_color
        
        self.fill_color: Color = fill_color
        self.icon_fill_color: Color = icon_fill_color
        
        self.cursor_icon_size: int = cursor_icon_size
        self.display_icon_size: Coords = display_icon_size
        self.gap: int = (self.rect.height - self.display_icon_size[1]) // 2
        self.tooltip_padding = tooltip_padding
        
        self.icons: Dict[str, Surface] = {}
        for icon_data in {
            "display": {"icons": display_icons, "size": self.display_icon_size},
            "cursor": {"icons": cursor_icons, "size": [self.cursor_icon_size,]*2}
        }.values():
            for filename in icon_data["icons"]:
                icon: Surface = None
                try:
                    image_name: str = path.basename(filename)
                    icon = ImageCache().get_image(
                        image_name,
                        True,
                        icon_data["size"]
                    )
                except pygame.error as e:
                    Logger.error(f"Error loading icon")
                    icon = None
                self.icons[filename] = icon
        
        self.cursor_pos: Coords = None
        self.cursor_icon_name: str = None
        
        self.tooltip_rect: Rect = None
        self.tooltip_surface: Surface = None
        
        
        self.display_data: List[Dict[str, Union[str, int, float, bool]]] = []
        
        self.relative_mouse_position: Coords = None
    
    def get_cursor_pos(self, absolute_mouse_pos: Optional[Coords] = None) -> Coords:
        if not absolute_mouse_pos:
            return self.cursor_pos
        return [
            absolute_mouse_pos[0] - (self.cursor_icon_size // 2),
            absolute_mouse_pos[1] - (self.cursor_icon_size // 2)
        ]
    
    def get_tooltip_pos(self, absolute_mouse_pos: Coords, tooltip_size: Coords) -> Coords:
        screen_rect = self.screen.get_rect(topleft=(0, 0))
        x = absolute_mouse_pos[0] + 2 * self.gap
        y = absolute_mouse_pos[1]

        # Check if the tooltip goes off the right edge of the screen
        if x + tooltip_size[0] + 2*self.tooltip_padding > screen_rect.right:
            x = absolute_mouse_pos[0] - tooltip_size[0] - 2 * self.gap  # Move tooltip to the left

        # Check if the tooltip goes off the bottom edge of the screen
        if y + tooltip_size[1] + 2*self.tooltip_padding > screen_rect.bottom:
            y = absolute_mouse_pos[1] - tooltip_size[1]  # Move tooltip above the mouse

        # Check if the tooltip goes off the top edge of the screen.
        if y - self.tooltip_padding < screen_rect.top:
            y = absolute_mouse_pos[1] + tooltip_size[1]

        return [x, y]

    def get_is_hovered(self, absolute_mouse_pos: Coords) -> bool:
        return self.rect.collidepoint(absolute_mouse_pos)

    def get_is_data_hovered(self, text_rect: Rect) -> bool:
        return text_rect.collidepoint(self.relative_mouse_pos)

    def get_relative_mouse_pos(self, absolute_mouse_pos: Coords) -> Coords:
        return [absolute_mouse_pos[0] - self.rect.x, absolute_mouse_pos[1] - self.rect.y]

    def set_tooltip_surface_rect(self, text: str, absolute_mouse_pos) -> None:
        self.tooltip_surface = FontManager().get_font(self.font_size, self.fill_color, text)
        self.tooltip_rect = Rect(
            *self.get_tooltip_pos(absolute_mouse_pos, self.tooltip_surface.get_size()),
            *self.tooltip_surface.get_size()
        )

    def _update(self,
        absolute_mouse_pos: Coords,
        icons: Tuple[str, str],
        data: List[Dict[str, Union[str, int, float, bool]]],
        tooltip_text: Optional[str] = None
    ) -> None:
        self.relative_mouse_pos = self.get_relative_mouse_pos(absolute_mouse_pos)
        # ANCHOR[id=DisplayUpdate]
        if tooltip_text:
            self.set_tooltip_surface_rect(tooltip_text, absolute_mouse_pos)
        else:
            self.tooltip_surface = None
            self.tooltip_rect = None
        
        self.cursor_pos = self.get_cursor_pos(absolute_mouse_pos)
        self.cursor_icon_name = icons.get("cursor")
        """
        TODO - Investigate if this data can be initialized and minimally updated (hint for example?)
        Maybe data can have aunique key in a dict.
        Since display icons can have the size, maybe their Surface can be pre-set.
        """
        width_acc = self.gap
        self.display_data = data
        for d in self.display_data:
            if d["type"] == "text":
                text_surface = FontManager().get_font(self.font_size, self.font_color, d["data"])
                text_rect: Rect = Rect(
                    width_acc - self.gap,
                    0,
                    text_surface.get_width() + 2*self.gap,
                    self.rect.height
                )
                width_acc += text_surface.get_width() + self.gap*2
                d["text_surface"] = text_surface
                d["text_rect"] = text_rect
                if self.get_is_data_hovered(text_rect):
                    hint: str = d["hint"]
                    self.set_tooltip_surface_rect(hint, absolute_mouse_pos)
                # pygame.draw.rect(self.surface, (0, 255, 0), text_rect, 2) # FIXME - DEBUG ONLY
            elif d["type"] == "icon":
                icon_image_surface: Surface = ImageCache().get_image(d["icon_name"], True, self.display_icon_size)
                icon_image_rect: Rect = Rect(
                    width_acc - self.gap,
                    0,
                    icon_image_surface.get_width() + 2*self.gap,
                    self.rect.height
                )
                width_acc += icon_image_surface.get_width() + self.gap*2
                d["icon_image_surface"] = icon_image_surface
                d["icon_image_rect"] = icon_image_rect
                if self.get_is_data_hovered(icon_image_rect):
                    hint: str = d["hint"]
                    self.set_tooltip_surface_rect(hint, absolute_mouse_pos)

    def draw(self) -> None:
        # ANCHOR[id=DisplayDraw]
        """
            Override draw so that cursor can be drawn later
        """
        self.fill(self.fill_color)
        self.draw_data()
        # self.screen.blit(self, self.rect.topleft)
    
    def draw_data(self):
        for d in self.display_data:
            if d["type"] == "text":
                self.blit(d["text_surface"], (
                    d["text_rect"].x + (d["text_rect"].width - d["text_surface"].get_width()) // 2,
                    (d["text_rect"].height - d["text_surface"].get_height()) // 2,
                    d["text_surface"].get_width(),
                    d["text_surface"].get_height()
                ))
            elif d["type"] == "icon":
                pygame.draw.rect(self.surface, self.icon_fill_color, (
                    d["icon_image_rect"].x + (d["icon_image_rect"].width - d["icon_image_surface"].get_width()) // 2,
                    (d["icon_image_rect"].height - d["icon_image_surface"].get_height()) // 2,
                    d["icon_image_surface"].get_width(),
                    d["icon_image_surface"].get_height()
                ), border_radius=2)
                self.blit(d["icon_image_surface"], (
                    d["icon_image_rect"].x + (d["icon_image_rect"].width - d["icon_image_surface"].get_width()) // 2,
                    (d["icon_image_rect"].height - d["icon_image_surface"].get_height()) // 2,
                    d["icon_image_surface"].get_width(),
                    d["icon_image_surface"].get_height()
                ))
    
    def draw_tooltip(self):
        if self.tooltip_surface and self.tooltip_rect:
            pygame.draw.rect(
                self.screen, self.font_color,
                (
                    self.tooltip_rect.left - self.tooltip_padding,
                    self.tooltip_rect.top - self.tooltip_padding,
                    self.tooltip_rect.width + 2* self.tooltip_padding,
                    self.tooltip_rect.height + 2*self.tooltip_padding,
                )
            )
            self.screen.blit(
                self.tooltip_surface,
                self.tooltip_rect
            )
    
    def draw_cursor(self):
        self.screen.blit(
            self.icons.get(self.cursor_icon_name),
            self.cursor_pos
        )