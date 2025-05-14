from typing import Callable, Dict, List, Optional, Union
from .utility import *
from .SurfaceRect import SurfaceRect
from .SubSurfaceRect import SubSurfaceRect
from .ImageCache import ImageCache
from .Logger import Logger
from os import path
from .ClickAnimatedSurface import ClickAnimatedSurface

class Control(SubSurfaceRect):
    # ANCHOR - Control
    
    def __init__(self,
        x: int, y: int, width: int, height: int, screen: Surface,
        button_size: List[int],
        icon_buttons: Dict[str, Callable],
        button_hover_callback: Callable,
        fill_color: str,
        button_fill_color: str
    ) -> None:
        super().__init__(x, y, width, height, screen)
        
        self.button_size = button_size
        
        self.gap = (self.rect.height - self.button_size[1]) // 2, 10
        
        self.fill_color = fill_color
        self.button_fill_color = button_fill_color
        
        self.buttons: Dict[str, Dict[str, Union[ClickAnimatedSurface, Rect, Callable, bool]]] = {}
        for icon_name, icon_button_dict in icon_buttons.items():
            button: Surface = None
            try:
                icon_animated_frame_suffixes: List[str] = icon_button_dict["animated_frame_suffixes"]
                button = ClickAnimatedSurface(
                    self, self.button_size, list(map(lambda n : ImageCache().get_image(f"{icon_name}_{n}.png", True, self.button_size), icon_animated_frame_suffixes))
                )
            except pygame.error as e:
                Logger.error(f"Error loading icon")
                button = None
            rect = Rect((
                self.rect.width - (self.gap[0] + self.button_size[0]) * (len(self.buttons) + 1),
                self.gap[1]
            ), self.button_size)
            self.buttons[icon_name] = {"button": button, "rect": rect, "callback": icon_button_dict["callback"], "disabled": False}
            
            self.button_hover_callback: Callable = button_hover_callback
            
            self.relative_mouse_pos = None
    
    def is_hovered(self, absolute_mouse_pos: Coords) -> bool:
        return self.rect.collidepoint(absolute_mouse_pos)

    def get_is_button_hovered(self, button_filename: str) -> bool:
        if self.relative_mouse_pos != None:
            return self.buttons[button_filename]["rect"].collidepoint(self.relative_mouse_pos)
        return False

    def get_relative_mouse_pos(self, absolute_mouse_pos: Coords) -> Coords:
        return [absolute_mouse_pos[0] - self.rect.x, absolute_mouse_pos[1] - self.rect.y]

    # ANCHOR[id=ControlUpdate]
    def _update(self,
        absolute_mouse_pos: Coords,
        event: Event,
        buttons: Dict[str, Dict[str, Union[str, bool]]]
    ):
        self.relative_mouse_pos = self.get_relative_mouse_pos(absolute_mouse_pos)
        for button_name, button_dict in self.buttons.items():
            button_dict["disabled"] = buttons.get(button_name) != None and buttons.get(button_name)["disabled"] == True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    if self.is_hovered(absolute_mouse_pos):
                        if not button_dict["disabled"]:
                            if self.get_is_button_hovered(button_name):
                                callback: Callable = button_dict["callback"]
                                button_dict["button"].start_animation(callback)
                
    
    # ANCHOR[id=ControlFixedUpdate]
    def fixed_update(self,
        buttons: Dict[str, Dict[str, bool]]
    ):
        for button_name, button_dict in self.buttons.items():
            button_dict["disabled"] = buttons.get(button_name) != None and buttons.get(button_name)["disabled"] == True
            button_dict["button"].update()
            if self.get_is_button_hovered(button_name):
                self.button_hover_callback(
                    {
                        True: buttons[button_name]["hint"]["disabled"],
                        False: buttons[button_name]["hint"]["enabled"]
                    }[button_dict["disabled"]]
                )

    # ANCHOR[id=ControlDraw]
    def _draw(self) -> None:
        if self.fill_color:
            self.fill(self.fill_color)
        
        for button_name, button_dict in self.buttons.items():
            self.draw_button(button_dict)
    
    def draw_button(self, button_dict: Dict[str, Union[ClickAnimatedSurface, Rect, Callable, bool]]) -> None:
        button_dict["button"].set_alpha(256 - (button_dict["disabled"] * 192))  # Add translucency
        pygame.draw.rect(self.surface, self.button_fill_color, button_dict["rect"], border_radius=2)
        button_dict["button"].draw(button_dict["rect"])
