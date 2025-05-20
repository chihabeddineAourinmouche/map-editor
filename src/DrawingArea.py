from math import ceil, floor
from os import path
from typing import Callable, List, Optional, Tuple, Union
from .utility import *
from .SpriteData import SpriteData
from .HitBoxData import HitBoxData
from .Sprite import Sprite
from .HitBox import HitBox
from .ImageCache import ImageCache

class DrawingArea(Rect):
    icon_size: Coords = None
    edge_margin: int = 50
    
    def __init__(self,
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
    ):
        # ANCHOR[id=DrawingAreaInit]
        super().__init__(x, y, width, height)
        
        self.screen: Surface = screen
        
        self.player_starting_pos: Coords = [INF, INF]
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
        self.canvas_rect: Rect = Rect(self.x, self.y, canvas_width, canvas_height)
        
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
        
        self.absolute_mouse_pos = [INF, INF]
        self.relative_mouse_pos: Coords = [INF, INF]
        self.canvas_mouse_pos: Coords = [INF, INF]
        
        self.start_pos: Coords = [INF, INF]
        self.current_pos: Coords = [INF, INF]
        self.selection_rect: Rect = None
        
        self.highlight_rects: List[Rect] = []
        self.highlight_color: Color = None
        self.highlight_outline_width: int = None
        
        self.temporary_sprites: List[Sprite] = []
        self.simple_click: bool = True
        
        self.is_sprite_mode = False
        self.is_hitbox_mode = False
        self.is_delete_mode = False
        self.is_player_mode = False
        self.is_move_mode = False
    
    def is_empty(self):
        return not(self.has_sprites() or self.has_hitboxes())
    
    def has_sprites(self) -> bool:
        return True if len(self.sprites) else False
    
    def has_hitboxes(self) -> bool:
        return True if len(self.hitboxes) else False

    
    
    def get_right_edge_rect(self) -> Rect:
        return Rect(
            self.width - self.edge_margin,
            1,
            self.edge_margin,
            self.height
        )
    
    def get_left_edge_rect(self) -> Rect:
        return Rect(
            1,
            1,
            self.edge_margin,
            self.height
        )
    
    def get_top_edge_rect(self) -> Rect:
        return Rect(
            1,
            1,
            self.width,
            self.edge_margin
        )
    
    def get_bottom_edge_rect(self) -> Rect:
        return Rect(
            1,
            self.height - self.edge_margin,
            self.width,
            self.edge_margin
        )
    
    def is_right_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[0] >= self.width - self.edge_margin
    
    def is_left_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[0] < self.edge_margin
    
    def is_top_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[1] < self.edge_margin
    
    def is_bottom_edge_hovered(self) -> bool:
        return self.relative_mouse_pos[1] >= self.height - self.edge_margin
    
    
    
    def get_sprite_by_id(self, _id) -> Union[Sprite, None]:
        sprites: List[Sprite] = list(filter(lambda sprite : sprite.get_id() == _id, self.sprites))
        return sprites[0] if len(sprites) else None
    
    def get_sprite_at(self) -> Union[Sprite, None]:
        sprites = list(filter(lambda s : s.collidepoint(add_list(self.canvas_mouse_pos, self.topleft)), reversed(self.sprites)))
        if len(sprites):
            return sprites[0]
        return None
    
    def get_sprite_id_at(self) -> Union[str, None]:
        sprite: Sprite = self.get_sprite_at()
        return sprite.get_id() if sprite else None
    
    def get_hitbox_at(self) -> Union[HitBox, None]:
        hitboxes = list(filter(lambda h : h.get_rect().collidepoint(add_list(self.canvas_mouse_pos, self.topleft)), reversed(self.hitboxes)))
        if len(hitboxes):
            return hitboxes[0]
        return None

    def get_hitbox_id_at(self) -> Union[str, None]:
        hitbox: HitBox = self.get_hitbox_at()
        return hitbox.get_id() if hitbox else None

    def get_hitboxes_within_rectangle(self, rect: Rect) -> List[HitBox]:
        return list(filter(lambda hitbox: rect.contains(hitbox.get_rect()), self.hitboxes))

    def get_hitboxes_intersecting_rectangle(self, rect: Rect) -> List[HitBox]:
        return list(filter(lambda hitbox: rect.colliderect(hitbox.get_rect()), self.hitboxes))

    def get_sprites_within_rectangle(self, rect: Rect) -> List[Sprite]:
        return list(filter(lambda sprite: rect.contains(sprite), self.sprites))
    
    def get_sprites_intersecting_rectangle(self, rect: Rect) -> List[Sprite]:
        return list(filter(lambda sprite: rect.colliderect(sprite), self.sprites))



    def get_canvas_viewport_rect(self) -> Rect:
        return Rect(
            *multiply_int(-1, self.panning_offset),
            *self.size
        )
    


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
    
    
    
    def get_is_drawing(self) -> bool:
        return self.is_drawing
    
    def get_is_deleting(self) -> bool:
        return self.is_deleting

    def get_is_panning(self) -> bool:
        return self.is_panning



    def is_hovered(self) -> bool:
        return self.collidepoint(self.absolute_mouse_pos)



    def calculate_snapping_coords(self, sprite_size: Optional[Coords]=None) -> Coords:
        # Calculate canvas coordinates of the mouse (where the sprite will be placed)
        if sprite_size != None:
            intended_canvas_pos = self.canvas_mouse_pos

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
            return add_list([final_canvas_x, final_canvas_y], self.topleft)
        return self.canvas_mouse_pos



    def get_canvas_mouse_pos(self) -> Coords:
        return add_list(add_list(self.absolute_mouse_pos, multiply_int(-1, self.panning_offset)), multiply_int(-1, self.topleft))

    def get_relative_mouse_pos(self) -> Coords:
        return add_list(self.absolute_mouse_pos, multiply_int(-1, self.topleft))
    
    
    
    def horizontal_scroll(self, direction: int):
        if direction < 0 or direction > 0:
            self.panning_offset[0] += floor(direction * self.scrolling_speed)
        
        #keep drawing_area canvas within viewport bounds
        if self.canvas_rect.width < self.width:
            self.panning_offset[0] = 0
        else:
            self.panning_offset[0] = max(self.width - self.canvas_rect.width, min(0, self.panning_offset[0]))
    
    def vertical_scroll(self, direction: int):
        if direction < 0 or direction > 0:
            self.panning_offset[1] += floor(direction * self.scrolling_speed)
        
        #keep drawing_area canvas within viewport bounds
        if self.canvas_rect.height < self.height:
            self.panning_offset[1] = 0
        else:
            self.panning_offset[1] = max(self.height - self.canvas_rect.height, min(0, self.panning_offset[1]))



    def resize_canvas(self, amount: Optional[Coords] = None, size: Optional[Coords] = None) -> Surface:
        self.canvas_rect.update(
            self.canvas_rect.topleft,
            add_list(self.canvas_rect.size, amount) if size == None else size
        )



    def load_sprites(self, data: List[SpriteData]):
        self.sprites = list(map(
        lambda s : Sprite(*s.get("coordinates"), self.screen, ImageCache().get_image(s.get("file_name")), s.get("file_name"), _id=s.get("id")),
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
        if data != None and data[0] != self.canvas_rect.width and data[1] != self.canvas_rect.height:
            self.resize_canvas(size=data)
        
    def load_data(self, data: Dict[str, Union[List[SpriteData], List[HitBoxData]]]):
        self.load_canvas_size(data.get("world_size"))
        self.load_sprites(data.get("sprites"))
        self.load_hitboxes(data.get("hitboxes"))
        self.load_player_starting_position(data.get("starting_position"))



    def add_hitbox(self, hitbox: HitBox) -> None:
        self.hitboxes.append(hitbox)

    def delete_hitbox(self, _id: str):
        self.hitboxes = list(filter(lambda hitbox : hitbox.get_id() != _id, self.hitboxes))

    def add_sprite(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)

    def delete_sprite(self, _id: str):
        self.sprites = list(filter(lambda sprite : sprite.get_id() != _id, self.sprites))



# ANCHOR[id=EventHandlers]
    def handle_mouse_button_down(self,
        event: Event,
        selected_sprite_id: str,
        sprites: List[Sprite],
        set_player_position: Callable[[Coords], None],
        right_click_callback: Callable,
        is_hovered: bool
    ):
        if is_hovered:
            selected_sprites = list(filter(lambda sprite : sprite.get_id() == selected_sprite_id, sprites))
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    if self.is_sprite_mode:
                        self.simple_click = True
                        if len(selected_sprites):
                            self.is_cloning = True
                            self.start_pos = self.calculate_snapping_coords()
                            self.current_pos = self.start_pos
                            print(self.start_pos[0], self.current_pos[0])
                            self.selection_rect = Rect(
                                *self.start_pos,
                                0, 0
                            )
                    elif self.is_hitbox_mode:
                        self.is_drawing = True
                        self.start_pos = self.canvas_mouse_pos
                        self.current_pos = self.canvas_mouse_pos
                        self.selection_rect = Rect(
                            *self.start_pos,
                            0, 0
                        )
                    elif self.is_delete_mode:
                        self.is_deleting = True
                        self.start_pos = self.canvas_mouse_pos
                        self.current_pos = self.canvas_mouse_pos
                        self.selection_rect = Rect(
                            *self.start_pos,
                            0, 0
                        )
                    elif self.is_player_mode:
                        self.player_starting_pos = self.canvas_mouse_pos # TODO - Should it be the center of the icon instead? INVESTIGATE!
                        set_player_position(self.canvas_mouse_pos)
                    elif self.is_move_mode:
                        sprite_id_to_move: str = self.get_sprite_id_at()
                        if sprite_id_to_move:
                            self.moving_sprite_id = sprite_id_to_move
                            list_containing_sprite_to_move: List[Sprite] = list(filter(lambda sprite : sprite.get_id() == self.moving_sprite_id, self.sprites))
                            if len(list_containing_sprite_to_move):
                                self.is_moving = True
                                sprite_to_move: Sprite = list_containing_sprite_to_move[0]
                                self.start_pos = sprite_to_move.topleft
                                self.current_pos = self.start_pos
                
                if event.button == MouseButtons.RIGHT:
                    if self.is_sprite_mode:
                        if self.is_cloning:
                            self.done_cloning()
                        else:
                            right_click_callback()
                    elif self.is_hitbox_mode:
                        if self.is_drawing:
                            self.done_drawing()
                        else:
                            right_click_callback()
                    elif self.is_delete_mode:
                        if self.is_deleting:
                            self.done_deleting()
                        else:
                            right_click_callback()
                    elif self.is_move_mode:
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
        is_hovered: bool
    ):
        if event.type == pygame.MOUSEMOTION:
            if not is_hovered:
                self.interrupt_moving_sprite()
                self.simple_click = False
              
            if self.is_sprite_mode:
                if self.is_cloning:
                    self.current_pos = self.calculate_snapping_coords()

                    w: int = abs(self.start_pos[0] - self.current_pos[0])
                    h: int = abs(self.start_pos[1] - self.current_pos[1])

                    rect_x: int = min(self.start_pos[0], self.current_pos[0]) + self.left
                    rect_y: int = min(self.start_pos[1], self.current_pos[1]) + self.top
                    self.selection_rect = Rect(rect_x, rect_y, w, h)

                    sprite_rect = self.ghost_sprite
                    sprite_width = sprite_rect.width
                    sprite_height = sprite_rect.height

                    """
                        Determine the drawing direction
                        If current_pos is >= start_pos, we are drawing in the positive direction (+1).
                        If current_pos is < start_pos, we are drawing in the negative direction (-1).
                    """
                    x_direction: int = 1 if self.current_pos[0] >= self.start_pos[0] else -1
                    y_direction: int = 1 if self.current_pos[1] >= self.start_pos[1] else -1

                    spawn_coverage_distance: float = 0.3
                    
                    def custom_coverage_round(value: float, threshold: Optional[float] = spawn_coverage_distance, direction: Optional[int] = 1) -> int:
                        return (ceil(value) if value - int(value) > threshold else floor(value)) + ((1-direction) // 2)

                    nb_sprites_to_draw_x: int = custom_coverage_round(w / sprite_width, direction=x_direction)
                    nb_sprites_to_draw_y: int = custom_coverage_round(h / sprite_height, direction=y_direction)

                    self.selection_rect.width += ((1-x_direction) // 2) * sprite_width
                    self.selection_rect.height += ((1-y_direction) // 2) * sprite_height

                    self.temporary_sprites = []

                    for i in range(nb_sprites_to_draw_x):
                        for j in range(nb_sprites_to_draw_y):
                            sprite_pos_x = (self.selection_rect.x if x_direction == 1 else self.selection_rect.width + self.selection_rect.x - sprite_width) + i * sprite_width * x_direction
                            sprite_pos_y = (self.selection_rect.y if y_direction == 1 else self.selection_rect.height + self.selection_rect.y - sprite_height) + j * sprite_height * y_direction

                            sprite: Sprite = Sprite(
                                sprite_pos_x,
                                sprite_pos_y,
                                self.screen,
                                self.ghost_sprite.get_image(),
                                self.ghost_sprite.get_name()
                            )
                            sprite.fixed_update(self.panning_offset, None)
                            self.temporary_sprites.append(sprite)
                            
                    if w > spawn_coverage_distance and h > spawn_coverage_distance:
                        self.simple_click = False
                        
            elif self.is_move_mode:
                if self.is_moving and self.start_pos:
                    moving_sprite: Union[Sprite, None] = self.get_sprite_by_id(self.moving_sprite_id)
                    if moving_sprite != None:
                        self.current_pos = self.calculate_snapping_coords(moving_sprite.size)
                        moving_sprite.set_top_left(self.current_pos)
                        moving_sprite.fixed_update(self.panning_offset, None)
                        self.highlight_rects = [moving_sprite]
                    else:
                        self.move_highlight_rects = []
                        
            elif (self.is_hitbox_mode and self.is_drawing) or (self.is_delete_mode and self.is_deleting):
                self.selection_rect = Rect(
                    *add_list([
                        min(self.start_pos[0], self.current_pos[0]),
                        min(self.start_pos[1], self.current_pos[1])
                    ], self.topleft),
                    abs(self.start_pos[0] - self.current_pos[0]),
                    abs(self.start_pos[1] - self.current_pos[1])
                )
            
            if self.is_panning:
                if self.start_pos:
                    delta = [self.relative_mouse_pos[0] - self.start_pos[0], self.relative_mouse_pos[1] - self.start_pos[1]]
                    self.panning_offset = [self.panning_offset[0] + delta[0], self.panning_offset[1] + delta[1]]
                    self.start_pos = self.relative_mouse_pos
                    
                    # Keep canvas within viewport bounds
                    if self.canvas_rect.width < self.width:
                        self.panning_offset[0] = 0
                    else:
                        self.panning_offset[0] = max(self.width - self.canvas_rect.width, min(0, self.panning_offset[0]))

                    if self.canvas_rect.height < self.height:
                        self.panning_offset[1] = 0
                    else:
                        self.panning_offset[1] = max(self.height - self.canvas_rect.height, min(0, self.panning_offset[1]))

    def handle_mouse_button_up(self,
        event: Event,
        selected_sprite_id: str,
        sprites: List[Sprite],
        add_data: Callable[[Union[SpriteData, HitBoxData], str], None],
        delete_data: Callable[[str, str], None],
        move_sprite: Callable[[str, Coords], None],
        is_hovered: bool
    ):
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == MouseButtons.LEFT:
                if self.is_sprite_mode:
                    sprite_rect: Rect = self.ghost_sprite
                    sprite_width: int = sprite_rect.width
                    sprite_height: int = sprite_rect.height
                    spawn_coverage_distance: float = 0.3
                    if self.is_cloning and self.selection_rect.width > spawn_coverage_distance * sprite_width and self.selection_rect.height > spawn_coverage_distance * sprite_height:
                        self.sprites += self.temporary_sprites
                        for sprite in self.temporary_sprites:
                            sprite.get_image().set_alpha(256)
                            add_data(sprite.get_data(), "sprite")
                    else:
                        if self.simple_click and is_hovered:
                            selected_sprites = list(filter(lambda sprite : sprite.get_id() == selected_sprite_id, sprites))
                            if len(selected_sprites):
                                sprite = Sprite(
                                    *self.calculate_snapping_coords(self.ghost_sprite.size),
                                    self.screen,
                                    ImageCache().get_image(selected_sprites[0].get_name()),
                                    selected_sprites[0].get_name()
                                )
                                sprite.fixed_update(self.panning_offset, None)
                                self.add_sprite(sprite)
                                add_data(sprite.get_data(), "sprite")
                    self.done_cloning()
                    # self.simple_click = True # Should be exactly here to reset simple click
                elif self.is_hitbox_mode:
                    if self.is_drawing and self.start_pos:
                        if self.selection_rect.width > 0 and self.selection_rect.height > 0:
                            hitbox = HitBox(
                                self.selection_rect.x,
                                self.selection_rect.y,
                                self.selection_rect.width,
                                self.selection_rect.height
                            )
                            hitbox.update(self.panning_offset)
                            self.add_hitbox(hitbox)
                            add_data(hitbox.get_data(), "hitbox")
                        self.done_drawing()
                elif self.is_delete_mode:
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
                elif self.is_move_mode:
                    if self.is_moving and self.current_pos and self.moving_sprite_id:
                        moving_sprite: Union[Sprite, None] = self.get_sprite_by_id(self.moving_sprite_id)
                        if moving_sprite != None:
                            move_sprite(self.moving_sprite_id, self.current_pos)
                            moving_sprite.get_image().set_alpha(256)
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
        sprites: Tuple[Sprite, ...],
        selected_sprite_id: str,
        is_hovered: bool
    ):
        if is_hovered:
            if self.is_sprite_mode:
                self.display_ghost_sprite = True
                selected_sprites = list(filter(lambda sprite : sprite.get_id() == selected_sprite_id, sprites))
                if len(selected_sprites) and not self.is_panning:
                    if self.ghost_sprite == None or self.ghost_sprite.get_id() != selected_sprite_id:
                        self.ghost_sprite = Sprite(
                            *selected_sprites[0].topleft,
                            self.screen,
                            ImageCache().get_image(selected_sprites[0].get_name()),
                            selected_sprites[0].get_name(),
                            selected_sprite_id
                        )
                    else:
                        self.ghost_sprite.set_image(self.ghost_sprite.get_image().copy())
                    self.ghost_sprite.set_top_left(self.calculate_snapping_coords(sprite_size=self.ghost_sprite.size))
        
        if not is_hovered or not self.is_sprite_mode or self.is_panning:
            self.display_ghost_sprite = False



    def update(self,
        event: Event,
        sprites: Tuple[Sprite, ...],
        selected_sprite_id: str,
        right_click_callback: Callable,
        add_data: Callable[[Union[SpriteData, HitBoxData], str], None],
        delete_data: Callable[[str, str], None],
        set_player_position: Callable[[Coords], None],
        move_sprite: Callable[[str, Coords], None]
    ) -> None:
        # ANCHOR[id=DrawingAreaUpdate]
        is_hovered: bool = self.is_hovered()
        
        self.handle_mouse_button_down(
            event,
            selected_sprite_id,
            sprites,
            set_player_position,
            right_click_callback,
            is_hovered,
        )

        self.handle_mouse_wheel(event, is_hovered)

        self.handle_mouse_button_up(
            event,
            selected_sprite_id,
            sprites,
            add_data,
            delete_data,
            move_sprite,
            is_hovered
        )

        self.handle_mouse_motion(
            event,
            is_hovered
        )

        self.update_ghost_sprite(
            sprites,
            selected_sprite_id,
            is_hovered
        )
    
        for sprite in self.sprites:
            sprite.update(event, lambda *args, **kwargs: None)



    def fixed_update(self,
        is_sprite_mode: bool,
        is_hitbox_mode: bool,
        is_delete_mode: bool,
        is_player_mode: bool,
        is_move_mode: bool,
        selected_sprite_id: str,
    ):
        # ANCHOR[id=DrawingAreaFixedUpdate]
        self.absolute_mouse_pos = pygame.mouse.get_pos()
        self.relative_mouse_pos = self.get_relative_mouse_pos()
        self.canvas_mouse_pos = self.get_canvas_mouse_pos()
        
        self.is_sprite_mode = is_sprite_mode
        self.is_hitbox_mode = is_hitbox_mode
        self.is_delete_mode = is_delete_mode
        self.is_player_mode = is_player_mode
        self.is_move_mode = is_move_mode
        
        if self.is_delete_mode:
            if not self.is_panning:
                if not self.is_deleting:
                    hitbox = self.get_hitbox_at()
                    if hitbox:
                        self.highlight_rects = [hitbox.get_rect()]
                    else:
                        sprite = self.get_sprite_at()
                        if sprite != None:
                            self.highlight_rects = [sprite]
                        else:
                            self.highlight_rects = []
                else:
                    self.highlight_rects = list(map(
                        lambda i : i.get_rect(),
                        self.get_hitboxes_within_rectangle(self.selection_rect)
                    )) + list(map(
                        lambda i : i,
                        self.get_sprites_within_rectangle(self.selection_rect)
                    ))
        
        if self.is_move_mode:
            if not self.is_panning:
                if not self.is_moving:
                    sprite = self.get_sprite_at()
                    if sprite != None:
                        self.highlight_rects = [sprite]
                    else:
                        self.highlight_rects = []
        
        if not (self.is_delete_mode or self.is_move_mode):
            self.highlight_rects = []
        
        self.highlight_color, self.highlight_outline_width = {
            (True, False): (self.delete_highlight_color, self.delete_selection_outline_width),
            (False, True): (self.move_highlight_color, self.move_selection_outline_width),
        }.get((self.is_delete_mode, self.is_move_mode), (None, None))
        
        if (self.is_deleting or self.is_drawing or self.is_panning) and self.start_pos:
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
        
        for hitbox in self.hitboxes:
            hitbox.update(self.panning_offset)
            
        for sprite in [*self.sprites, self.ghost_sprite] if self.ghost_sprite != None else self.sprites:
            sprite.fixed_update(self.panning_offset, None)



    def draw_hitboxes(self) -> None:
        for hitbox in self.get_hitboxes_intersecting_rectangle(self.get_canvas_viewport_rect()):
            hitbox.draw(self.screen)

    def draw_selection_rect(self) -> None:
        if self.selection_rect:
            color: Color = None
            outline_width: int = None
            (color, outline_width) = {
                (True, False, False): (self.preview_hitbox_outline_color, self.preview_hitbox_outline_width),
                (False, True, False): (self.delete_selection_outline_color, self.delete_selection_outline_width),
                (False, False, True): (self.clone_selection_outline_color, self.clone_selection_outline_width),
            }.get((self.is_drawing, self.is_deleting, self.is_cloning), ((0, 0, 0, 0), 0)) # Else transparent, no width
            
            offset_selection_rect: Rect = Rect(*add_list(self.selection_rect.topleft, self.panning_offset), *self.selection_rect.size)
            
            x, y, width, height = offset_selection_rect
            
            self.selection_rect_alpha_surface = Surface(offset_selection_rect.size, pygame.SRCALPHA)
            self.selection_rect_alpha_surface.set_alpha(64)
            pygame.draw.rect(self.selection_rect_alpha_surface, color, (0, 0, width, height))
            self.screen.blit(self.selection_rect_alpha_surface, offset_selection_rect)
            
            pygame.draw.rect(self.screen, color, offset_selection_rect, outline_width)

            if self.is_drawing:
                pygame.draw.line(self.screen, color, (x, y), (x + width - 1, y + height - 1), outline_width)
                pygame.draw.line(self.screen, color, (x, y + height - 1), (x + width - 1, y), outline_width)

    def draw_sprites(self) -> None:
        for sprite in self.get_sprites_intersecting_rectangle(self.get_canvas_viewport_rect()):
            sprite.draw()

    def draw_grid(self) -> None:
        if self.canvas_grid_cell_size is not None and self.canvas_grid_cell_size > 0:
            width = self.canvas_rect.width
            height = self.canvas_rect.height

            for x in range(self.x + self.panning_offset[0], width, self.canvas_grid_cell_size):
                if x > self.x and x < self.x + self.width:
                    pygame.draw.line(self.screen, self.canvas_grid_color, (x, self.panning_offset[1]), (x, height + self.panning_offset[1]))

            for y in range(self.y + self.panning_offset[1], height, self.canvas_grid_cell_size):
                if y > self.y and y < self.y + self.height:
                    pygame.draw.line(self.screen, self.canvas_grid_color, (self.panning_offset[0], y), (width + self.panning_offset[0], y))

    def draw_highlight_rects(self):
        for rect in self.highlight_rects:
            offset_highlight_rect: Rect = Rect(*add_list(rect.topleft, self.panning_offset), *rect.size)
            pygame.draw.rect(
                self.screen,
                self.highlight_color,
                offset_highlight_rect,
                self.highlight_outline_width
            )

    def draw_bottom_right_round_corner(self):
        border_radius: int = 10
        self.screen.fill(self.canvas_grid_color)
        pygame.draw.rect(self.screen, self.canvas_fill_color, self, border_bottom_right_radius=border_radius)

    def draw_player_starting_pos(self):
        if self.player_starting_pos:
            self.screen.blit(
                self.icon_player_position,
                (
                    self.player_starting_pos[0] - self.icon_player_position.get_rect().width // 2,
                    self.player_starting_pos[1] - self.icon_player_position.get_rect().height // 2,
                )
            )

    def draw_ghost_sprite(self):
        if self.display_ghost_sprite and self.ghost_sprite and not self.is_cloning:
            # Draw translucent box
            self.ghost_sprite.get_image().set_alpha(128)  # 50% translucent
            self.ghost_sprite.draw()

    def draw_temporary_sprites(self):
        for sprite in self.temporary_sprites:
            sprite.draw()

    def draw(self) -> None:
    # ANCHOR[id=DrawingAreaDraw]
        self.draw_bottom_right_round_corner()
        self.draw_grid()
        self.draw_sprites()
        self.draw_ghost_sprite()
        self.draw_hitboxes()
        self.draw_temporary_sprites()
        self.draw_selection_rect()
        self.draw_highlight_rects()
        self.draw_player_starting_pos()



# LINK #DrawingAreaInit
# LINK #EventHandlers
# LINK #DrawingAreaUpdate
# LINK #DrawingAreaFixedUpdate
# LINK #DrawingAreaDraw