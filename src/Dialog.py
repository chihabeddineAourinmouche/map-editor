from typing import Callable, Dict, Optional, Union
from .utility import *
from .SurfaceRect import SurfaceRect
from .FontManager import FontManager

class Dialog(SurfaceRect):
    
    overlay_fill_color: Color
    box_fill_color: Color
    max_box_width: int
    max_box_height: int
    font_color: Color
    font_size: int
    font_family: str
    button_width: int
    button_height: int
    box_padding_pct: float
    inter_button_gap: int
    min_message_top_padding: int
    min_button_bottom_padding: int
    
    def __init__(
        self,
        screen: Surface,
        message: str,
        options: Dict[str, Dict[str, Union[Surface, Rect, str, bool, Callable]]]
    ):
        super().__init__(*screen.get_rect(topleft=(0, 0)), screen)

        self.overlay: Surface = Surface(self.rect.size, pygame.SRCALPHA)
        self.overlay.set_alpha(220)
        self.overlay.fill(self.overlay_fill_color)
        
        self.message_text = FontManager().get_font(
            self.font_size,
            self.font_color,
            message
        )
        
        dialog_box_width = min(int(self.screen.get_width() * self.box_padding_pct), self.max_box_width)
        dislog_box_height = min(int(self.screen.get_height() * self.box_padding_pct), self.max_box_height)
        self.dialog_box_rect: Rect = Rect(
            (self.rect.width - dialog_box_width) // 2, 
            (self.rect.height - dislog_box_height) // 2, 
            min(int(self.screen.get_width() * self.box_padding_pct), self.max_box_width),
            min(int(self.screen.get_height() * self.box_padding_pct), self.max_box_height)
        )
        self.dialog_box_surface: Surface = Surface(self.dialog_box_rect.size, pygame.SRCALPHA)
        
        self.buttons: Dict[str, Dict[str, Union[Surface, Rect, str, Callable]]] = options
        for i, button_dict in enumerate(self.buttons.values()):
            """
                Button rects are relative to dialog box,
                so positioning starts at 0 on the x-axis.
            """
            wrapping_rect_x: int = (i * (self.dialog_box_rect.width // len(options)))
            button_dict["surface"] = Surface((self.button_width, self.button_height), pygame.SRCALPHA)
            button_dict["rect"] = Rect(
                wrapping_rect_x + ((self.dialog_box_rect.width // len(options)) - self.button_width) // 2,
                max(
                    int((self.dialog_box_rect.height) *.85 - self.button_height), 
                    int((self.dialog_box_rect.height) *.85 - self.button_height) - self.min_button_bottom_padding
                ),
                self.button_width,
                self.button_height
            )
        
        self.init: bool = False
        self.relative_mouse_pos: Coords = None

    def is_hovered(self, mouse_pos: Optional[Coords] = None) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def get_relative_mouse_pos(self, mouse_pos: Coords) -> Coords:
        """ Override get_relative_mouse_pos """
        return [mouse_pos[0] - self.dialog_box_rect.topleft[0], mouse_pos[1] - self.dialog_box_rect.topleft[1]]

    def is_button_hovered(self, label: str) -> bool:
        return self.buttons[label]["rect"].collidepoint(self.relative_mouse_pos)

    def _update(self,
        absolute_mouse_pos: Coords,
        event: Event,
        close_callback: Callable
    ) -> None:
        self.relative_mouse_pos = self.get_relative_mouse_pos(absolute_mouse_pos)
        # ANCHOR[id=DialogUpdate]
        if self.is_hovered(absolute_mouse_pos):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    if not self.dialog_box_rect.collidepoint(absolute_mouse_pos):
                        close_callback()
                elif event.button == MouseButtons.RIGHT:
                    close_callback()
            elif event.type == pygame.KEYDOWN:
                if event.key == KeyboardKeys.ESCAPE:
                    close_callback()
            
            for label, button_dict in self.buttons.items():
                if self.is_button_hovered(label):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == MouseButtons.LEFT:
                            callback: Callable = button_dict["callback"]
                            callback()

    def draw_button(self, label: str, button_dict: Dict[str, Union[Surface, Rect, str, bool, Callable]]):
        pygame.draw.rect(
            button_dict["surface"],
            self.font_color,
            (0, 0, *button_dict["rect"].size),
            2-(2*button_dict["filled"])
        )
        button_text: Surface = FontManager().get_font(
            self.font_size,
            self.font_color if not button_dict["filled"] else self.box_fill_color,
            label.capitalize()
        )
        button_dict["surface"].blit(
            button_text,
            (
                (button_dict["rect"].width - button_text.get_width()) // 2,
                (button_dict["rect"].height - button_text.get_height()) // 2,
            )
        )
        self.dialog_box_surface.blit(button_dict["surface"], button_dict["rect"])
    
    def draw_dialog_box(self):
        self.dialog_box_surface.fill(self.box_fill_color, (0, 0, *self.dialog_box_rect.size))
        
        self.dialog_box_surface.blit(
            self.message_text,
            (
                (self.dialog_box_rect.width - self.message_text.get_width()) // 2,
                min((self.dialog_box_rect.height - self.message_text.get_rect().height) // 2, self.min_message_top_padding)
            )
        )
        
        for label, button_dict in self.buttons.items():
            self.draw_button(label, button_dict)
        
        self.blit(self.dialog_box_surface, self.dialog_box_rect)

    def _draw(self):
        # ANCHOR[id=DialogDraw]
        if not self.init:
            self.init = True
            
            self.blit(self.overlay, self.rect.topleft)
            
            self.draw_dialog_box()
