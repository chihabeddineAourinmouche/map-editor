from os import path
from typing import Callable, List, Optional, Tuple, Union
from .utility import *
from .SurfaceRect import SurfaceRect
from .SpriteData import SpriteData
from .HitBoxData import HitBoxData
from .Sprite import Sprite
from .HitBox import HitBox
from .ImageCache import ImageCache

class DrawingArea(SurfaceRect):
    # ANCHOR - DrawingArea
    
    icon_size: Coords = None
    
    def __init__(
        self,
        x: int, y: int, width: int, height: int,
        screen: Surface,
        canvas_width: int, canvas_height: int,
        canvas_fill_color: Color,
        preview_hit_box_outline_color: Color,
        delete_selection_outline_color: Color,
        preview_hit_box_outline_width: int,
        delete_selection_outline_width: int,
        canvas_grid_cell_size: int,
        canvas_grid_color: Color,
        snap_threshold: int,
        delete_highlight_color: Color,
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
        self.preview_hit_box_outline_color: Color = preview_hit_box_outline_color
        self.delete_selection_outline_color: Color = delete_selection_outline_color
        self.preview_hit_box_outline_width: int = preview_hit_box_outline_width
        self.delete_selection_outline_width: int = delete_selection_outline_width
        
        self.canvas_grid_cell_size: int = canvas_grid_cell_size
        self.canvas_grid_color = canvas_grid_color
        self.canvas: Surface = Surface((canvas_width, canvas_height), pygame.SRCALPHA)
        
        self.snap_threshold: int = snap_threshold
        
        self.is_hovered: bool = False
        
        self.is_panning: bool = False
        self.panning_start_pos: Coords = None
        self.panning_offset: Coords = [0, 0]
        
        self.scrolling_speed: int = scrolling_speed
        
        self.sprites: List[Sprite] = []
        self.ghost_sprite: Sprite = None
        self.display_ghost_sprite = False
        self.ghost_sprite_alpha_surface: Surface = Surface((0, 0), pygame.SRCALPHA)
        
        self.delete_highlight_rect: Rect = None
        self.delete_highlight_rects: List[Rect] = []
        self.delete_highlight_color: Color = delete_highlight_color
        
        self.hitboxes: List[HitBox] = []
        
        self.start_hitbox_drawing_pos: Coords = None
        self.current_hitbox_drawing_pos: Coords = None
        self.is_drawing_hitbox: bool = False
        
        self.start_deleting_pos: Coords = None
        self.current_deleting_pos: Coords = None
        self.is_deleting = False
        
        self.hitbox_preview_delete_selection_alpha_surface: Surface = None
        self.hitbox_preview_delete_selection_rect: Rect = None
        
        self.relative_mouse_pos: Coords = None
        self.canvas_mouse_pos: Coords = None
    
    def is_empty(self):
        return len(self.sprites) + len(self.hitboxes) == 0
    
    def get_sprite_at(self) -> Sprite:
        sprites = list(filter(lambda s : s.get_sprite_rect(s.get_sprite_rect().topleft).collidepoint(self.canvas_mouse_pos), reversed(self.sprites)))
        if len(sprites):
            return sprites[0]
        return None
    
    def get_sprite_id_at(self) -> str:
        sprite: Sprite = self.get_sprite_at()
        return sprite.get_id() if sprite else None
    
    def get_hitbox_at(self) -> HitBox:
        hitboxes = list(filter(lambda h : h.get_rect().collidepoint(self.canvas_mouse_pos), reversed(self.hitboxes)))
        if len(hitboxes):
            return hitboxes[0]
        return None

    def get_hitboxes_within_rectangle(self, rect: Rect) -> List[HitBox]:
        return list(filter(lambda hitbox: rect.contains(hitbox.get_rect()), self.hitboxes))

    def get_hitboxes_intersecting_rectangle(self, rect: Rect) -> List[HitBox]:
        return list(filter(lambda hitbox: rect.colliderect(hitbox.get_rect()), self.hitboxes))

    def get_sprites_within_rectangle(self, rect: Rect) -> List[Sprite]:
        return list(filter(lambda sprite: rect.contains(sprite.get_sprite_rect()), self.sprites))
    
    def get_sprites_intersecting_rectangle(self, rect: Rect) -> List[Sprite]:
        return list(filter(lambda sprite: rect.colliderect(sprite.get_sprite_rect()), self.sprites))

    def get_viewport_rect(self) -> Rect:
        return Rect(
            *multiply_int(-1, self.panning_offset),
            *self.rect.size
        )

    def get_hitbox_id_at(self) -> str:
        hitbox: HitBox = self.get_hitbox_at()
        return hitbox.get_id() if hitbox else None

    def interrupt_drawing_hitbox(self) -> None:
        self.is_drawing_hitbox = False
        self.start_hitbox_drawing_pos = None
        self.current_hitbox_drawing_pos = None
        self.hitbox_preview_delete_selection_rect = None

    def interrupt_deleting(self) -> None:
        self.is_deleting = False
        self.start_deleting_pos = None
        self.current_deleting_pos = None
        self.hitbox_preview_delete_selection_rect = None
        self.delete_highlight_rects = []
        self.delete_highlight_rect = None
    
    def get_is_drawing_hitbox(self) -> bool:
        return self.is_drawing_hitbox
    
    def get_is_deleting(self) -> bool:
        return self.is_deleting

    def get_is_panning(self) -> bool:
        return self.is_panning

    def get_is_hovered(self, recheck: Optional[bool] = False) -> bool:
        self.is_hovered = Rect(
            0, 0,
            min(self.canvas.get_rect(topleft=self.panning_offset).width, self.get_width()),
            min(self.canvas.get_rect(topleft=self.panning_offset).height, self.get_height())
        ).collidepoint(self.relative_mouse_pos) if recheck else self.is_hovered
        return self.is_hovered

    def calculate_snapping_coords(self) -> Coords:
        # Calculate canvas coordinates of the mouse (where the sprite will be placed)
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
        return [final_canvas_x, final_canvas_y]

    def get_mouse_position_on_canvas(self) -> Coords:
        return [self.relative_mouse_pos[0] - self.panning_offset[0], self.relative_mouse_pos[1] - self.panning_offset[1]]

    def get_relative_mouse_pos(self, absolute_mouse_pos: Coords) -> Coords:
        return [absolute_mouse_pos[0] - self.rect.topleft[0], absolute_mouse_pos[1] - self.rect.topleft[1]]

    def horizontal_scroll(self, direction: int):
        if direction < 0:
            self.panning_offset[0] += direction * self.scrolling_speed
        elif direction > 0:
            self.panning_offset[0] += direction * self.scrolling_speed
        
        #keep sprite_panel canvas within viewport bounds
        canvas_rect = self.canvas.get_rect()
        viewport = self.rect
        if canvas_rect.width < viewport.width:
            self.panning_offset[0] = 0
        else:
            self.panning_offset[0] = max(viewport.width - canvas_rect.width, min(0, self.panning_offset[0]))
    
    def vertical_scroll(self, direction: int):
        if direction < 0:
            self.panning_offset[1] += direction * self.scrolling_speed
        elif direction > 0:
            self.panning_offset[1] += direction * self.scrolling_speed
        
        #keep sprite_panel canvas within viewport bounds
        canvas_rect = self.canvas.get_rect()
        viewport = self.rect
        if canvas_rect.height < viewport.height:
            self.panning_offset[1] = 0
        else:
            self.panning_offset[1] = max(viewport.height - canvas_rect.height, min(0, self.panning_offset[1]))

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
        
    def load_data(self, data: Dict[str, Union[List[SpriteData], List[HitBoxData]]]):
        self.load_sprites(data.get("sprites"))
        self.load_hitboxes(data.get("hitboxes"))
        self.load_player_starting_position(data.get("starting_position"))

    def _update(self,
        absolute_mouse_pos: Coords,
        event: Event,
        is_sprite_mode: bool,
        is_hitbox_mode: bool,
        is_delete_mode: bool,
        is_player_mode: bool,
        sprites: Tuple[Sprite, ...],
        selected_sprite_id: str,
        right_click_callback: Callable,
        add_data: Callable[[Union[SpriteData, HitBoxData], str], None],
        delete_data: Callable[[str, str], None],
        set_player_position: Callable[[Coords], None]
    ) -> None:
        # ANCHOR[id=DrawingAreaUpdate]
        self.relative_mouse_pos = self.get_relative_mouse_pos(absolute_mouse_pos)
        self.canvas_mouse_pos = self.get_mouse_position_on_canvas()
        
        if self.get_is_hovered(True):
            selected_sprites = list(filter(lambda sprite : sprite.get_id() == selected_sprite_id, sprites))
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.LEFT:
                    if is_sprite_mode:
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
                    elif is_hitbox_mode:
                        self.is_drawing_hitbox = True
                        self.start_hitbox_drawing_pos = self.canvas_mouse_pos
                        self.current_hitbox_drawing_pos = self.canvas_mouse_pos
                    elif is_delete_mode:
                        self.is_deleting = True
                        self.start_deleting_pos = self.canvas_mouse_pos
                        self.current_deleting_pos = self.canvas_mouse_pos
                    elif is_player_mode:
                        self.player_starting_pos = self.canvas_mouse_pos
                        set_player_position(self.canvas_mouse_pos)
                
                if event.button == MouseButtons.RIGHT:
                    if is_hitbox_mode:
                        if self.is_drawing_hitbox:
                            self.interrupt_drawing_hitbox()
                        else:
                            right_click_callback()
                    elif is_delete_mode:
                        if self.is_deleting:
                            self.interrupt_deleting()
                        else:
                            right_click_callback()
                    else:
                            right_click_callback()
                
                if event.button == MouseButtons.MIDDLE:
                    self.is_panning = True
                    self.panning_start_pos = self.relative_mouse_pos

            if event.type == pygame.MOUSEWHEEL:
                keys_pressed = pygame.key.get_pressed()
                if keys_pressed[KeyboardKeys.LEFT_ALT]:
                    self.horizontal_scroll(event.y)
                else:
                    self.vertical_scroll(event.y)

            if is_delete_mode:
                if not self.is_panning:
                    if not self.hitbox_preview_delete_selection_rect:
                        hitbox = self.get_hitbox_at()
                        if hitbox:
                            self.delete_highlight_rect = hitbox.get_rect()
                        else:
                            self.delete_highlight_rect = None
                            sprite = self.get_sprite_at()
                            if sprite != None:
                                self.delete_highlight_rect = sprite.get_sprite_rect(topleft=sprite.get_sprite_rect().topleft)
                            else:
                                self.delete_highlight_rect = None
                    else:
                        self.delete_highlight_rects = list(map(
                            lambda i : i.get_rect(),
                            self.get_hitboxes_within_rectangle(self.hitbox_preview_delete_selection_rect)
                        )) + list(map(
                            lambda i : i.get_sprite_rect(),
                            self.get_sprites_within_rectangle(self.hitbox_preview_delete_selection_rect)
                        ))
                else:
                    self.delete_highlight_rect = None
                    self.delete_highlight_rects = []
            else:
                self.delete_highlight_rect = None
                self.delete_highlight_rects = []

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

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == MouseButtons.LEFT:
                if is_hitbox_mode:
                    if self.is_drawing_hitbox and self.start_hitbox_drawing_pos:
                        if self.get_is_hovered(True):
                            x = min(self.start_hitbox_drawing_pos[0], self.canvas_mouse_pos[0])
                            y = min(self.start_hitbox_drawing_pos[1], self.canvas_mouse_pos[1])
                            width = abs(self.start_hitbox_drawing_pos[0] - self.canvas_mouse_pos[0])
                            height = abs(self.start_hitbox_drawing_pos[1] - self.canvas_mouse_pos[1])
                            if width > 0 and height > 0:
                                hitbox = HitBox(x, y, width, height)
                                self.add_hitbox(hitbox)
                                add_data(hitbox.get_data(), "hitbox")
                            self.interrupt_drawing_hitbox()
                elif is_delete_mode:
                    if self.is_deleting and self.start_deleting_pos:
                        x = min(self.start_deleting_pos[0], self.canvas_mouse_pos[0])
                        y = min(self.start_deleting_pos[1], self.canvas_mouse_pos[1])
                        width = abs(self.start_deleting_pos[0] - self.canvas_mouse_pos[0])
                        height = abs(self.start_deleting_pos[1] - self.canvas_mouse_pos[1])
                        if width > 0 and height > 0:
                            hitboxes: List[HitBox] = self.get_hitboxes_within_rectangle(Rect(x, y, width, height))
                            sprites: List[Sprite] = self.get_sprites_within_rectangle(Rect(x, y, width, height))
                            for hitbox_id in list(map(lambda hitbox : hitbox.get_id(), hitboxes)):
                                self.delete_hitbox(hitbox_id)
                                delete_data(hitbox_id, "hitbox")
                            
                            for sprite_id in list(map(lambda sprite : sprite.get_id(), sprites)):
                                self.delete_sprite(sprite_id)
                                delete_data(sprite_id, "sprite")
                                
                        elif width == 0 and height == 0:
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
                        self.interrupt_deleting()
            
            if event.button == MouseButtons.MIDDLE:
                self.is_panning = False
                self.panning_start_pos = None

        if event.type == pygame.MOUSEMOTION:
            if not pygame.mouse.get_pressed()[1]:
                self.is_panning = False
                self.panning_start_pos = None
                
            if is_hitbox_mode:
                if self.is_drawing_hitbox and self.start_hitbox_drawing_pos:
                    self.current_hitbox_drawing_pos = self.canvas_mouse_pos
                    x = min(self.start_hitbox_drawing_pos[0], self.current_hitbox_drawing_pos[0])
                    y = min(self.start_hitbox_drawing_pos[1], self.current_hitbox_drawing_pos[1])
                    width = abs(self.start_hitbox_drawing_pos[0] - self.current_hitbox_drawing_pos[0])
                    height = abs(self.start_hitbox_drawing_pos[1] - self.current_hitbox_drawing_pos[1])
                    self.hitbox_preview_delete_selection_rect = Rect(x, y, width, height)
            elif is_delete_mode:
                if self.is_deleting and self.start_deleting_pos:
                    self.current_deleting_pos = self.canvas_mouse_pos
                    x = min(self.start_deleting_pos[0], self.current_deleting_pos[0])
                    y = min(self.start_deleting_pos[1], self.current_deleting_pos[1])
                    width = abs(self.start_deleting_pos[0] - self.current_deleting_pos[0])
                    height = abs(self.start_deleting_pos[1] - self.current_deleting_pos[1])
                    self.hitbox_preview_delete_selection_rect = Rect(x, y, width, height)

            if self.is_panning:
                if self.panning_start_pos:
                    delta = [self.relative_mouse_pos[0] - self.panning_start_pos[0], self.relative_mouse_pos[1] - self.panning_start_pos[1]]
                    self.panning_offset = [self.panning_offset[0] + delta[0], self.panning_offset[1] + delta[1]]
                    self.panning_start_pos = self.relative_mouse_pos
                    
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

        if not self.get_is_hovered(True) or not is_sprite_mode or self.is_panning:
            self.display_ghost_sprite = False
    
    def fixed_update(self):
        absolute_mouse_pos: Coords = pygame.mouse.get_pos()
        direction_x: int = None
        # [dx,dy]=[cx−sx,cy−sy]
        if self.is_drawing_hitbox and (absolute_mouse_pos[0] >= self.rect.x + self.rect.width or absolute_mouse_pos[0] <= self.rect.x):
            direction_x: int = self.current_hitbox_drawing_pos[0] - self.start_hitbox_drawing_pos[0]
        elif self.is_deleting and (absolute_mouse_pos[0] >= self.rect.x + self.rect.width or absolute_mouse_pos[0] <= self.rect.x):
            direction_x: int = self.current_deleting_pos[0] - self.start_deleting_pos[0]

        if direction_x != None and abs(direction_x) > 0:
            direction_x = abs(direction_x) / direction_x
            if absolute_mouse_pos[0] >= self.rect.x + self.rect.width:
                direction_x = 1
            elif absolute_mouse_pos[0] <= self.rect.x:
                direction_x = -1
            self.horizontal_scroll(-direction_x)

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

    def draw_preview_selection(self) -> None:
        if self.hitbox_preview_delete_selection_rect:
            color: Color = self.preview_hit_box_outline_color if self.is_drawing_hitbox else self.delete_selection_outline_color
            outline_width: int = self.preview_hit_box_outline_width if self.is_drawing_hitbox else self.delete_selection_outline_width
            if self.is_hovered:
                pass
            x, y, width, height = list(self.hitbox_preview_delete_selection_rect)
            if self.is_drawing_hitbox:
                pygame.draw.line(self.canvas, color, (x, y), (x + width - 1, y + height - 1), outline_width)
                pygame.draw.line(self.canvas, color, (x, y + height - 1), (x + width - 1, y), outline_width)
            else:
                self.hitbox_preview_delete_selection_alpha_surface = Surface(self.hitbox_preview_delete_selection_rect.size, pygame.SRCALPHA)
                self.hitbox_preview_delete_selection_alpha_surface.set_alpha(64)
                pygame.draw.rect(self.hitbox_preview_delete_selection_alpha_surface, color, (0, 0, width, height))
                self.canvas.blit(self.hitbox_preview_delete_selection_alpha_surface, (x, y, width, height))
            pygame.draw.rect(self.canvas, color, (x, y, width, height), outline_width)

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

    def draw_preview_sprite(self):
        if self.display_ghost_sprite and self.ghost_sprite:
            # Draw translucent box
            self.ghost_sprite.set_alpha(128)  # 50% translucent
            ghost_sprite_rect: Rect = self.ghost_sprite.get_sprite_rect(topleft=self.ghost_sprite.get_sprite_rect().topleft)
            self.ghost_sprite.draw()

    def draw_delete_highlight(self):
        if self.hitbox_preview_delete_selection_rect:
            for rect in self.delete_highlight_rects:
                pygame.draw.rect(self.canvas, self.delete_highlight_color, rect, 2)

        if self.delete_highlight_rect:
            pygame.draw.rect(self.canvas, self.delete_highlight_color, self.delete_highlight_rect, self.delete_selection_outline_width)
    
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

    def _draw(self) -> None:
    # ANCHOR[id=DrawingAreaDraw]

        self.draw_bottom_right_round_corner()
        self.draw_grid()
        self.draw_sprites()
        self.draw_preview_sprite()
        self.draw_hitboxes()
        self.draw_player_starting_pos()
        self.draw_preview_selection()
        self.draw_delete_highlight()
        self.draw_canvas()

# LINK #DrawingAreaUpdate
# LINK #DrawingAreaDraw