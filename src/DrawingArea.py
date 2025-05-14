from math import floor
from os import path
from typing import Callable, List, Optional, Tuple, Union
from .utility import *
from .SurfaceRect import SurfaceRect
from .SubSurfaceRect import SubSurfaceRect
from .SpriteData import SpriteData
from .HitBoxData import HitBoxData
from .Sprite import Sprite
from .HitBox import HitBox
from .ImageCache import ImageCache

class DrawingArea(SubSurfaceRect):
    # ANCHOR - DrawingArea
    icon_size: Coords = None
    
    def __init__(
        self,
        x: int, y: int, width: int, height: int,
        screen: Surface,
        canvas_width: int, canvas_height: int,
        canvas_fill_color: Color,
        preview_hitbox_outline_color: Color,
        delete_selection_outline_color: Color,
        clone_selection_outline_color: Color,
        preview_hitbox_outline_width: int,
        delete_selection_outline_width: int,
        move_selection_outline_width: int,
        clone_selection_outline_width: int,
        canvas_grid_cell_size: int,
        canvas_grid_color: Color,
        snap_threshold: int,
        delete_highlight_color: Color,
        move_highlight_color: Color,
        scrolling_speed: int,
        player_position_icon: str
    ) -> None:
        super().__init__(x, y, width, height, screen)
        
        self.player_starting_pos: Coords = None
        self.icon_player_position: Surface = None
        try:
            self.icon_player_position = ImageCache().get_image(
                path.basename(player_position_icon),
                True,
                self.icon_size
            )
        except pygame.error as e:
            Logger.error(f"Error loading icon")
            self.icon_player_position = None
        
        self.canvas_fill_color: Color = canvas_fill_color
        
        self.preview_hitbox_outline_color: Color = preview_hitbox_outline_color
        self.preview_hitbox_outline_width: int = preview_hitbox_outline_width
        
        self.delete_selection_outline_color: Color = delete_selection_outline_color
        self.delete_selection_outline_width: int = delete_selection_outline_width

        self.delete_highlight_color: Color = delete_highlight_color
        
        self.move_selection_outline_width: int = move_selection_outline_width
        self.move_highlight_color: Color = move_highlight_color
        
        self.clone_selection_outline_color: Color = clone_selection_outline_color
        self.clone_selection_outline_width: int = clone_selection_outline_width
        
        self.canvas_grid_cell_size: int = canvas_grid_cell_size
        self.canvas_grid_color = canvas_grid_color
        self.canvas: Surface = Surface((canvas_width, canvas_height), pygame.SRCALPHA)
        
        self.snap_threshold: int = snap_threshold
        
        self.is_panning: bool = False
        self.panning_offset: Coords = [0, 0]
        
        self.scrolling_speed: int = scrolling_speed
        
        self.sprites: List[Sprite] = []
        self.hitboxes: List[HitBox] = []
        
        self.ghost_sprite: Sprite = None
        self.display_ghost_sprite = False
        
        self.is_drawing: bool = False
        self.is_deleting: bool = False
        self.is_moving: bool = False
        self.is_cloning: bool = False
        
        self.moving_sprite_id: str = None
        
        self.selection_rect_alpha_surface: Surface = None
        
        self.relative_mouse_pos: Coords = None
        self.canvas_mouse_pos: Coords = None
        
        self.start_pos: Coords = None
        self.current_pos: Coords = None
        self.selection_rect: Rect = None
        
        self.highlight_rects: List[Rect] = []
        self.highlight_color: Color = None
        self.highlight_outline_width: int = None
        
        self.temporary_sprites: List[Sprite] = []
        self.simple_click = True
    
    def is_empty(self):
        return len(self.sprites) + len(self.hitboxes) == 0
    
    def get_right_edge_rect(self) -> Rect:
        return Rect(
            self.rect.width - 50,
            1,
            50,
            self.rect.height
        )
    
    def get_left_edge_rect(self) -> Rect:
        return Rect(
            1,
            1,
            50,
            self.rect.height
        )
    
    def get_top_edge_rect(self) -> Rect:
        return Rect(
            1,
            1,
            self.rect.width,
            50
        )
    
    def get_bottom_edge_rect(self) -> Rect:
        return Rect(
            1,
            self.rect.height - 50,
            self.rect.width,
            50
        )
    
    def is_right_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[0] >= self.rect.width - 50
    
    def is_left_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[0] < 50
    
    def is_top_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[1] < 50
    
    def is_bottom_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[1] >= self.rect.height - 50
    
    def get_sprite_by_id(self, _id) -> Union[Sprite, None]:
        sprites: List[Sprite] = list(filter(lambda sprite : sprite.get_id() == _id, self.sprites))
        return sprites[0] if len(sprites) else None
    
    def get_sprite_at(self) -> Union[Sprite, None]:
        sprites = list(filter(lambda s : s.get_sprite_rect(s.get_sprite_rect().topleft).collidepoint(self.canvas_mouse_pos), reversed(self.sprites)))
        if len(sprites):
            return sprites[0]
        return None
    
    def get_sprite_id_at(self) -> Union[str, None]:
        sprite: Sprite = self.get_sprite_at()
        return sprite.get_id() if sprite else None
    
    def get_hitbox_at(self) -> Union[HitBox, None]:
        hitboxes = list(filter(lambda h : h.get_rect().collidepoint(self.canvas_mouse_pos), reversed(self.hitboxes)))
        if len(hitboxes):
            return hitboxes[0]
        return None

    def get_hitboxes_within_rectangle(self, rect: Rect) -> List[HitBox]:
        return list(filter(lambda hitbox: rect.contains(hitbox.get_rect()), self.hitboxes))

    def get_hitboxes_intersecting_rectangle(self, rect: Rect) -> List[HitBox]:
        return list(filter(lambda hitbox: rect.colliderect(hitbox.get_rect()), self.hitboxes))

    def has_sprites(self) -> bool:
        return True if len(self.sprites) else False

    def get_sprites_within_rectangle(self, rect: Rect) -> List[Sprite]:
        return list(filter(lambda sprite: rect.contains(sprite.get_sprite_rect()), self.sprites))
    
    def get_sprites_intersecting_rectangle(self, rect: Rect) -> List[Sprite]:
        return list(filter(lambda sprite: rect.colliderect(sprite.get_sprite_rect()), self.sprites))

    def get_viewport_rect(self) -> Rect:
        return Rect(
            *multiply_int(-1, self.panning_offset),
            *self.rect.size
        )

    def get_hitbox_id_at(self) -> Union[str, None]:
        hitbox: HitBox = self.get_hitbox_at()
        return hitbox.get_id() if hitbox else None
    
    def interrupt_selection(self):
        self.start_pos = None
        self.current_pos = None
        self.selection_rect = None

    def done_drawing(self) -> None:
        self.is_drawing = False

    def done_deleting(self) -> None:
        self.is_deleting = False
        self.highlight_rects = []
    
    def done_moving_sprite(self):
        self.is_moving = False
        self.moving_sprite_id = None

    def interrupt_moving_sprite(self):
        moving_sprite: Union[Sprite, None] = self.get_sprite_by_id(self.moving_sprite_id)
        if moving_sprite != None:
            moving_sprite.set_top_left(self.start_pos)
        self.done_moving_sprite()

    def done_cloning(self):
        self.is_cloning = False
        self.temporary_sprites = []
    
    def get_is_drawing_hitbox(self) -> bool:
        return self.is_drawing
    
    def get_is_deleting(self) -> bool:
        return self.is_deleting

    def get_is_panning(self) -> bool:
        return self.is_panning

    def is_hovered(self) -> bool:
        return Rect(
            0, 0,
            min(self.canvas.get_rect(topleft=self.panning_offset).width, self.get_width()),
            min(self.canvas.get_rect(topleft=self.panning_offset).height, self.get_height())
        ).collidepoint(self.relative_mouse_pos) if self.relative_mouse_pos else False

    def calculate_snapping_coords(self) -> Coords:
        # Calculate canvas coordinates of the mouse (where the sprite will be placed)
        if self.ghost_sprite != None:
            intended_canvas_pos = [
                self.canvas_mouse_pos[0] - self.ghost_sprite.get_sprite_rect().width // 2,
                self.canvas_mouse_pos[1] - self.ghost_sprite.get_sprite_rect().height // 2
            ]

            # Calculate the closest grid point
            closest_grid_x = round(intended_canvas_pos[0] / self.canvas_grid_cell_size) * self.canvas_grid_cell_size
            closest_grid_y = round(intended_canvas_pos[1] / self.canvas_grid_cell_size) * self.canvas_grid_cell_size

            # Calculate the distance to the closest grid point
            distance_x = abs(intended_canvas_pos[0] - closest_grid_x)
            distance_y = abs(intended_canvas_pos[1] - closest_grid_y)

            # Snap to grid if within the threshold
            if distance_x <= self.snap_threshold:
                final_canvas_x = closest_grid_x
            else:
                final_canvas_x = intended_canvas_pos[0]
                
            if distance_y <= self.snap_threshold:
                final_canvas_y = closest_grid_y
            else:
                final_canvas_y = intended_canvas_pos[1]

            # Convert the final canvas position back to screen coordinates for add_sprite and return
            return [final_canvas_x, final_canvas_y]
        return self.canvas_mouse_pos

    def get_mouse_position_on_canvas(self) -> Coords:
        if self.relative_mouse_pos != None:
            return [self.relative_mouse_pos[0] - self.panning_offset[0], self.relative_mouse_pos[1] - self.panning_offset[1]]
        return [0, 0]

    def get_relative_mouse_pos(self, absolute_mouse_pos: Coords) -> Coords:
        return [absolute_mouse_pos[0] - self.rect.topleft[0], absolute_mouse_pos[1] - self.rect.topleft[1]]

    def horizontal_scroll(self, direction: int):
        if direction < 0:
            self.panning_offset[0] += floor(direction * self.scrolling_speed)
        elif direction > 0:
            self.panning_offset[0] += floor(direction * self.scrolling_speed)
        
        #keep sprite_panel canvas within viewport bounds
        canvas_rect = self.canvas.get_rect()
        viewport = self.rect
        if canvas_rect.width < viewport.width:
            self.panning_offset[0] = 0
        else:
            self.panning_offset[0] = max(viewport.width - canvas_rect.width, min(0, self.panning_offset[0]))
    
    def vertical_scroll(self, direction: int):
        if direction < 0:
            self.panning_offset[1] += floor(direction * self.scrolling_speed)
        elif direction > 0:
            self.panning_offset[1] += floor(direction * self.scrolling_speed)
        
        #keep sprite_panel canvas within viewport bounds
        canvas_rect = self.canvas.get_rect()
        viewport = self.rect
        if canvas_rect.height < viewport.height:
            self.panning_offset[1] = 0
        else:
            self.panning_offset[1] = max(viewport.height - canvas_rect.height, min(0, self.panning_offset[1]))
    
    def resize_canvas(self, amount: Optional[Coords] = None, size: Optional[Coords] = None) -> Surface:
        new_canvas: Surface = Surface((
            self.canvas.get_rect().width + amount[0],
            self.canvas.get_rect().height + amount[1]
        ) if size == None else size, pygame.SRCALPHA)
        new_canvas.blit(self.canvas, (0, 0))
        return new_canvas
    
    def load_sprites(self, data: List[SpriteData]):
        self.sprites = list(map(
        lambda s : Sprite(*s.get("coordinates"), self.canvas, ImageCache().get_image(s.get("file_name")), s.get("file_name"), _id=s.get("id")),
        data
    ))
    
    def load_hitboxes(self, data: List[HitBoxData]):
        self.hitboxes = list(map(
            lambda h : HitBox(*h.get("rect"), _id=h.get("id")),
            data
        ))
    
    def load_player_starting_position(self, data: Coords):
        self.player_starting_pos = data
    
    def load_canvas_size(self, data: Coords):
        if data != None and data[0] != self.canvas.get_rect().width and data[1] != self.canvas.get_rect().height:
            self.canvas = self.resize_canvas(size=data)
        
    def load_data(self, data: Dict[str, Union[List[SpriteData], List[HitBoxData]]]):
        self.load_canvas_size(data.get("world_size"))
        self.load_sprites(data.get("sprites"))
        self.load_hitboxes(data.get("hitboxes"))
        self.load_player_starting_position(data.get("starting_position"))

# ANCHOR[id=EventHandlers]
    def handle_mouse_button_down(self,
        event: Event,
        selected_sprite_id: str,
        sprites: List[Sprite],
        is_sprite_mode: bool,
        is_hitbox_mode: bool,
        is_delete_mode: bool,
        is_player_mode: bool,
        is_move_mode: bool,
        set_player_position: Callable[[Coords], None],
        right_click_callback: Callable,
        is_hovered: bool
    ):
        if is_hovered:
            selected_sprites = list(filter(lambda sprite : sprite.get_id() == selected_sprite_id, sprites))
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    if is_sprite_mode:
                        if len(selected_sprites):
                            self.is_cloning = True
                            self.start_pos = [
                                self.canvas_mouse_pos[0] - (self.ghost_sprite.get_sprite_rect().width // 2),
                                self.canvas_mouse_pos[1] - (self.ghost_sprite.get_sprite_rect().height // 2),
                            ]
                            self.current_pos = [
                                self.canvas_mouse_pos[0] - (self.ghost_sprite.get_sprite_rect().width // 2),
                                self.canvas_mouse_pos[1] - (self.ghost_sprite.get_sprite_rect().height // 2),
                            ]
                            self.selection_rect = Rect(
                                *self.start_pos,
                                0, 0
                            )
                    elif is_hitbox_mode:
                        self.is_drawing = True
                        self.start_pos = self.canvas_mouse_pos
                        self.current_pos = self.canvas_mouse_pos
                        self.selection_rect = Rect(
                            *self.start_pos,
                            0, 0
                        )
                    elif is_delete_mode:
                        self.is_deleting = True
                        self.start_pos = self.canvas_mouse_pos
                        self.current_pos = self.canvas_mouse_pos
                        self.selection_rect = Rect(
                            *self.start_pos,
                            0, 0
                        )
                    elif is_player_mode:
                        self.player_starting_pos = self.canvas_mouse_pos
                        set_player_position(self.canvas_mouse_pos)
                    elif is_move_mode:
                        sprite_id_to_move: str = self.get_sprite_id_at()
                        if sprite_id_to_move:
                            self.moving_sprite_id = sprite_id_to_move
                            list_containing_sprite_to_move: List[Sprite] = list(filter(lambda sprite : sprite.get_id() == self.moving_sprite_id, self.sprites))
                            if len(list_containing_sprite_to_move):
                                self.is_moving = True
                                sprite_to_move: Sprite = list_containing_sprite_to_move[0]
                                self.start_pos = sprite_to_move.get_sprite_rect().topleft
                                self.current_pos = self.canvas_mouse_pos
                
                if event.button == MouseButtons.RIGHT:
                    if is_sprite_mode:
                        if self.is_cloning:
                            self.done_cloning()
                        else:
                            right_click_callback()
                    elif is_hitbox_mode:
                        if self.is_drawing:
                            self.done_drawing()
                        else:
                            right_click_callback()
                    elif is_delete_mode:
                        if self.is_deleting:
                            self.done_deleting()
                        else:
                            right_click_callback()
                    elif is_move_mode:
                        if self.is_moving:
                            self.interrupt_moving_sprite()
                        else:
                            right_click_callback()
                    else:
                            right_click_callback()
                
                if event.button == MouseButtons.MIDDLE:
                    self.is_panning = True
                    self.start_pos = self.relative_mouse_pos

    def handle_mouse_motion(self,
        event: Event,
        is_sprite_mode: bool,
        is_hitbox_mode: bool,
        is_delete_mode: bool,
        is_move_mode: bool,
        is_hovered: bool
    ):
        if event.type == pygame.MOUSEMOTION:
            if not is_hovered:
                self.interrupt_moving_sprite()
              
            if is_sprite_mode:
                if self.is_cloning:
                    self.current_pos = [
                        self.canvas_mouse_pos[0] - (self.ghost_sprite.get_sprite_rect().width // 2),
                        self.canvas_mouse_pos[1] - (self.ghost_sprite.get_sprite_rect().height // 2),
                    ]
                    x: int = min(self.start_pos[0], self.current_pos[0])
                    y: int = min(self.start_pos[1], self.current_pos[1])
                    w: int = abs(self.start_pos[0] - self.current_pos[0])
                    h: int = abs(self.start_pos[1] - self.current_pos[1])
                    self.selection_rect = Rect(x, y, w, h)
                    nb_sprites_to_draw_x: int = w // self.ghost_sprite.get_sprite_rect().width
                    nb_sprites_to_draw_y: int = h // self.ghost_sprite.get_sprite_rect().height
                    self.temporary_sprites = []
                    for i in range(nb_sprites_to_draw_x):
                        for j in range(nb_sprites_to_draw_y):
                            self.temporary_sprites.append(
                                Sprite(
                                    x + i * self.ghost_sprite.get_sprite_rect().width,
                                    y + j * self.ghost_sprite.get_sprite_rect().height,
                                    self.canvas,
                                    self.ghost_sprite.get_image(),
                                    self.ghost_sprite.get_name()
                                )
                            )
                    if w > 0 and h > 0:
                        self.simple_click = False
                    
            elif is_move_mode:
                if self.is_moving and self.start_pos:
                    moving_sprite: Union[Sprite, None] = self.get_sprite_by_id(self.moving_sprite_id)
                    if moving_sprite != None:
                        self.current_pos = self.calculate_snapping_coords()
                        moving_sprite.set_top_left(self.current_pos)
                        self.highlight_rects = [moving_sprite.get_sprite_rect(moving_sprite.topleft)]
                    else:
                        self.move_highlight_rects = []
                        
            elif (is_hitbox_mode and self.is_drawing) or (is_delete_mode and self.is_deleting):
                self.selection_rect = Rect(
                    min(self.start_pos[0], self.current_pos[0]),
                    min(self.start_pos[1], self.current_pos[1]),
                    abs(self.start_pos[0] - self.current_pos[0]),
                    abs(self.start_pos[1] - self.current_pos[1])
                )
            
            if self.is_panning:
                if self.start_pos:
                    delta = [self.relative_mouse_pos[0] - self.start_pos[0], self.relative_mouse_pos[1] - self.start_pos[1]]
                    self.panning_offset = [self.panning_offset[0] + delta[0], self.panning_offset[1] + delta[1]]
                    self.start_pos = self.relative_mouse_pos
                    
                    # Keep canvas within viewport bounds
                    canvas_rect = self.canvas.get_rect()
                    if canvas_rect.width < self.rect.width:
                        self.panning_offset[0] = 0
                    else:
                        self.panning_offset[0] = max(self.rect.width - canvas_rect.width, min(0, self.panning_offset[0]))

                    if canvas_rect.height < self.rect.height:
                        self.panning_offset[1] = 0
                    else:
                        self.panning_offset[1] = max(self.rect.height - canvas_rect.height, min(0, self.panning_offset[1]))

    def handle_mouse_button_up(self,
        event: Event,
        selected_sprite_id: str,
        sprites: List[Sprite],
        is_sprite_mode: bool,
        is_hitbox_mode: bool,
        is_delete_mode: bool,
        is_move_mode: bool,
        add_data: Callable[[Union[SpriteData, HitBoxData], str], None],
        delete_data: Callable[[str, str], None],
        move_sprite: Callable[[str, Coords], None],
        is_hovered: bool
    ):
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == MouseButtons.LEFT:
                if is_sprite_mode:
                    if self.is_cloning and self.selection_rect.width > 0 and self.selection_rect.height > 0:
                        self.sprites += self.temporary_sprites
                    else:
                        if self.simple_click and is_hovered:
                            selected_sprites = list(filter(lambda sprite : sprite.get_id() == selected_sprite_id, sprites))
                            if len(selected_sprites):
                                snapping_coords = self.calculate_snapping_coords()
                                sprite = Sprite(
                                    *snapping_coords,
                                    self.canvas,
                                    ImageCache().get_image(selected_sprites[0].get_name()),
                                    selected_sprites[0].get_name()
                                )
                                self.add_sprite(sprite)
                                add_data(sprite.get_data(), "sprite")
                    self.done_cloning()
                    self.simple_click = True # Should be exactly here to reset simple click
                elif is_hitbox_mode:
                    if self.is_drawing and self.start_pos:
                        if self.selection_rect.width > 0 and self.selection_rect.height > 0:
                            hitbox = HitBox(
                                self.selection_rect.x,
                                self.selection_rect.y,
                                self.selection_rect.width,
                                self.selection_rect.height
                            )
                            self.add_hitbox(hitbox)
                            add_data(hitbox.get_data(), "hitbox")
                        self.done_drawing()
                elif is_delete_mode:
                    if self.is_deleting and self.start_pos:
                        if self.selection_rect.width > 0 and self.selection_rect.height > 0:
                            hitboxes: List[HitBox] = self.get_hitboxes_within_rectangle(self.selection_rect)
                            sprites: List[Sprite] = self.get_sprites_within_rectangle(self.selection_rect)
                            for hitbox_id in list(map(lambda hitbox : hitbox.get_id(), hitboxes)):
                                self.delete_hitbox(hitbox_id)
                                delete_data(hitbox_id, "hitbox")
                            
                            for sprite_id in list(map(lambda sprite : sprite.get_id(), sprites)):
                                self.delete_sprite(sprite_id)
                                delete_data(sprite_id, "sprite")
                                
                        elif self.selection_rect.width == 0 and self.selection_rect.height == 0:
                            hitbox_id = self.get_hitbox_id_at()
                            if hitbox_id != None:
                                self.delete_hitbox(hitbox_id)
                                delete_data(hitbox_id, "hitbox")
                            else:
                                """
                                    I know that hitboxes always overlay sprites. So, in order to avoid accidentally deleting a
                                    sprite while attempting to delete a hitbox, only delete a sprite if no hitbox was found
                                    over it.
                                """
                                sprite_id = self.get_sprite_id_at()
                                if sprite_id != None:
                                    self.delete_sprite(sprite_id)
                                    delete_data(sprite_id, "sprite")
                        self.done_deleting()
                elif is_move_mode:
                    if self.is_moving and self.current_pos and self.moving_sprite_id:
                        moving_sprite: Union[Sprite, None] = self.get_sprite_by_id(self.moving_sprite_id)
                        if moving_sprite != None:
                            move_sprite(self.moving_sprite_id, self.current_pos)
                            self.done_moving_sprite()
            
            if event.button == MouseButtons.MIDDLE:
                self.is_panning = False
                self.interrupt_selection()

    def handle_mouse_wheel(self,
        event: Event,
        is_hovered: bool
    ):
        if is_hovered:
            if event.type == pygame.MOUSEWHEEL:
                keys_pressed = pygame.key.get_pressed()
                if keys_pressed[KeyboardKeys.LEFT_ALT]:
                    self.horizontal_scroll(event.y)
                else:
                    self.vertical_scroll(event.y)

    def update_ghost_sprite(self,
        is_sprite_mode: bool,
        sprites: Tuple[Sprite, ...],
        selected_sprite_id: str,
        is_hovered: bool
    ):
        if is_hovered:
            if is_sprite_mode:
                self.display_ghost_sprite = True
                selected_sprites = list(filter(lambda sprite : sprite.get_id() == selected_sprite_id, sprites))
                if len(selected_sprites) and not self.is_panning:
                    if self.ghost_sprite == None or self.ghost_sprite.get_id() != selected_sprite_id:
                        self.ghost_sprite = Sprite(
                            *selected_sprites[0].get_sprite_rect().topleft,
                            self.canvas,
                            ImageCache().get_image(selected_sprites[0].get_name()),
                            selected_sprites[0].get_name(),
                            selected_sprite_id
                        )
                    else:
                        self.ghost_sprite.set_image(self.ghost_sprite.get_image().copy())
                    self.ghost_sprite.set_top_left(self.calculate_snapping_coords())
        
        if not is_hovered or not is_sprite_mode or self.is_panning:
            self.display_ghost_sprite = False


    def _update(self,
        absolute_mouse_pos: Coords,
        event: Event,
        is_sprite_mode: bool,
        is_hitbox_mode: bool,
        is_delete_mode: bool,
        is_player_mode: bool,
        is_move_mode: bool,
        sprites: Tuple[Sprite, ...],
        selected_sprite_id: str,
        right_click_callback: Callable,
        add_data: Callable[[Union[SpriteData, HitBoxData], str], None],
        delete_data: Callable[[str, str], None],
        set_player_position: Callable[[Coords], None],
        move_sprite: Callable[[str, Coords], None]
    ) -> None:
        # ANCHOR[id=DrawingAreaUpdate]
        self.relative_mouse_pos = self.get_relative_mouse_pos(absolute_mouse_pos)
        self.canvas_mouse_pos = self.get_mouse_position_on_canvas()
        
        is_hovered: bool = self.is_hovered()
        
        self.handle_mouse_button_down(
            event,
            selected_sprite_id,
            sprites,
            is_sprite_mode,
            is_hitbox_mode,
            is_delete_mode,
            is_player_mode,
            is_move_mode,
            set_player_position,
            right_click_callback,
            is_hovered,
        )

        self.handle_mouse_wheel(event, is_hovered)

        self.handle_mouse_button_up(
            event,
            selected_sprite_id,
            sprites,
            is_sprite_mode,
            is_hitbox_mode,
            is_delete_mode,
            is_move_mode,
            add_data,
            delete_data,
            move_sprite,
            is_hovered
        )

        self.handle_mouse_motion(
            event,
            is_sprite_mode,
            is_hitbox_mode,
            is_delete_mode,
            is_move_mode,
            is_hovered
        )

        self.update_ghost_sprite(
            is_sprite_mode,
            sprites,
            selected_sprite_id,
            is_hovered
        )
            

    def fixed_update(self,
        is_delete_mode: bool,
        is_move_mode: bool
    ):
        # ANCHOR[id=DrawingAreaFixedUpdate]
        if is_delete_mode:
            if not self.is_panning:
                if not self.is_deleting:
                    hitbox = self.get_hitbox_at()
                    if hitbox:
                        self.highlight_rects = [hitbox.get_rect()]
                    else:
                        sprite = self.get_sprite_at()
                        if sprite != None:
                            self.highlight_rects = [sprite.get_sprite_rect(topleft=sprite.get_sprite_rect().topleft)]
                        else:
                            self.highlight_rects = []
                else:
                    self.highlight_rects = list(map(
                        lambda i : i.get_rect(),
                        self.get_hitboxes_within_rectangle(self.selection_rect)
                    )) + list(map(
                        lambda i : i.get_sprite_rect(),
                        self.get_sprites_within_rectangle(self.selection_rect)
                    ))
        
        if is_move_mode:
            if not self.is_panning:
                if not self.is_moving:
                    sprite = self.get_sprite_at()
                    if sprite != None:
                        self.highlight_rects = [sprite.get_sprite_rect(topleft=sprite.get_sprite_rect().topleft)]
                    else:
                        self.highlight_rects = []
        
        if not (is_delete_mode or is_move_mode):
            self.highlight_rects = []
        
        self.highlight_color, self.highlight_outline_width = {
            (True, False): (self.delete_highlight_color, self.delete_selection_outline_width),
            (False, True): (self.move_highlight_color, self.move_selection_outline_width),
        }.get((is_delete_mode, is_move_mode), (None, None))
        
        if (self.is_deleting or self.is_drawing or self.is_moving or self.is_panning) and self.start_pos:
            self.current_pos = self.canvas_mouse_pos

        if not (self.is_drawing or self.is_deleting or self.is_moving or self.is_cloning):
            if not self.is_panning:
                self.interrupt_selection()
        else:
            if self.is_right_edge_hovered():
                self.horizontal_scroll(-1*0.02)
            elif self.is_left_edge_hovered():
                self.horizontal_scroll(1*0.02)
            if self.is_bottom_edge_hovered():
                self.vertical_scroll(-1*0.02)
            elif self.is_top_edge_hovered():
                self.vertical_scroll(1*0.02)


    def add_hitbox(self, hitbox: HitBox) -> None:
        self.hitboxes.append(hitbox)

    def delete_hitbox(self, _id: str):
        self.hitboxes = list(filter(lambda hitbox : hitbox.get_id() != _id, self.hitboxes))

    def add_sprite(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)

    def delete_sprite(self, _id: str):
        self.sprites = list(filter(lambda sprite : sprite.get_id() != _id, self.sprites))

    def draw_canvas(self) -> None:
        visible_canvas_rect = Rect(0, 0, *self.rect.size).clip(self.canvas.get_rect())
        canvas_offset_x = visible_canvas_rect.x - self.canvas.get_rect().x - self.panning_offset[0]
        canvas_offset_y = visible_canvas_rect.y - self.canvas.get_rect().y - self.panning_offset[1]
        self.blit(
            self.canvas,
            self.get_rect(),
            area=(canvas_offset_x, canvas_offset_y, *self.rect.size)
        )

    def draw_hitboxes(self) -> None:
        for hitbox in self.get_hitboxes_intersecting_rectangle(self.get_viewport_rect()):
            hitbox.draw(self.canvas)

    def draw_selection_rect(self) -> None:
        if self.selection_rect:
            color: Color = None
            outline_width: int = None
            (color, outline_width) = {
                (True, False, False): (self.preview_hitbox_outline_color, self.preview_hitbox_outline_width),
                (False, True, False): (self.delete_selection_outline_color, self.delete_selection_outline_width),
                (False, False, True): (self.clone_selection_outline_color, self.clone_selection_outline_width),
            }.get((self.is_drawing, self.is_deleting, self.is_cloning), ((0, 0, 0, 0), 0)) # Else transparent, no width
            x, y, width, height = list(self.selection_rect)
            self.selection_rect_alpha_surface = Surface(self.selection_rect.size, pygame.SRCALPHA)
            self.selection_rect_alpha_surface.set_alpha(64)
            pygame.draw.rect(self.selection_rect_alpha_surface, color, (0, 0, width, height))
            self.canvas.blit(self.selection_rect_alpha_surface, self.selection_rect)
            pygame.draw.rect(self.canvas, color, self.selection_rect, outline_width)
            if self.is_drawing:
                pygame.draw.line(self.canvas, color, (x, y), (x + width - 1, y + height - 1), outline_width)
                pygame.draw.line(self.canvas, color, (x, y + height - 1), (x + width - 1, y), outline_width)

    def draw_sprites(self) -> None:
        for sprite in self.get_sprites_intersecting_rectangle(self.get_viewport_rect()):
            sprite.draw()

    def draw_grid(self) -> None:
        if self.canvas_grid_cell_size is not None and self.canvas_grid_cell_size > 0:
            width = self.canvas.get_width()
            height = self.canvas.get_height()
            for x in range(0, width, self.canvas_grid_cell_size):
                pygame.draw.line(self.canvas, self.canvas_grid_color, (x, 0), (x, height))
            for y in range(0, height, self.canvas_grid_cell_size):
                pygame.draw.line(self.canvas, self.canvas_grid_color, (0, y), (width, y))

    def draw_ghost_sprite(self):
        if self.display_ghost_sprite and self.ghost_sprite and not self.is_cloning:
            # Draw translucent box
            self.ghost_sprite.set_alpha(128)  # 50% translucent
            self.ghost_sprite.draw()

    def draw_highlight_rects(self):
        for rect in self.highlight_rects:
            pygame.draw.rect(
                self.canvas,
                self.highlight_color,
                rect,
                self.highlight_outline_width
            )
    
    def draw_bottom_right_round_corner(self):
        border_radius: int = 10
        self.canvas.fill(self.canvas_grid_color)
        self.fill(self.canvas_grid_color)
        pygame.draw.rect(self.canvas, self.canvas_fill_color, (
            - self.panning_offset[0] - border_radius,
            - self.panning_offset[1] - border_radius,
            min(self.rect.width, self.canvas.get_width()) + border_radius,
            min(self.rect.height, self.canvas.get_height()) + border_radius
        ), border_radius=border_radius)
    
    def draw_player_starting_pos(self):
        if self.player_starting_pos:
            self.canvas.blit(
                self.icon_player_position,
                (
                    self.player_starting_pos[0] - self.icon_player_position.get_rect().width // 2,
                    self.player_starting_pos[1] - self.icon_player_position.get_rect().height // 2,
                )
            )

    def draw_temporary_sprites(self):
        for sprite in self.temporary_sprites:
            sprite.draw()

    def _draw(self) -> None:
    # ANCHOR[id=DrawingAreaDraw]
        self.draw_bottom_right_round_corner()
        self.draw_grid()
        self.draw_sprites()
        self.draw_ghost_sprite()
        self.draw_hitboxes()
        self.draw_selection_rect()
        self.draw_highlight_rects()
        self.draw_temporary_sprites()
        self.draw_player_starting_pos()
        self.draw_canvas()

# LINK #EventHandlers
# LINK #DrawingAreaUpdate
# LINK #DrawingAreaFixedUpdate
# LINK #DrawingAreaDraw