from typing import Callable
from .utility import *

class ClickAnimatedSurface(Surface):
    def __init__(self, screen: Surface, icon_size: Coords, animated_frames: List[Surface], animation_frame_delay: Optional[int]=10):
        super().__init__(icon_size, pygame.SRCALPHA) # Use SRCALPHA for transparency
        
        self.screen = screen

        self.animation_frames = animated_frames

        # --- Initial State ---
        self.current_frame_index = 0

        # --- Animation State ---
        self.is_animating = False
        self.animation_frame_delay = animation_frame_delay
        self.frame_counter = 0
        self.end_animation_callback: Callable = None

    def start_animation(self, end_animation_callback: Callable):
        """Starts the animation sequence."""
        if not self.is_animating:
            self.is_animating = True
            self.frame_counter = 0 # Reset frame counter
            self.end_animation_callback = end_animation_callback

    def update(self):
        if self.is_animating:
            self.frame_counter += 1

            if self.frame_counter >= self.animation_frame_delay:
                self.frame_counter = 0 # Reset frame counter

                self.current_frame_index += 1 # Move to the next frame

                # Check if we have reached the end of the animation sequence
                if self.current_frame_index >= len(self.animation_frames):
                    # Animation finished, reset to the first frame
                    self.current_frame_index = 0
                    self.is_animating = False # Stop animating
                    if self.end_animation_callback:
                        self.end_animation_callback()
                        self.end_animation_callback = None

    def draw_frame(self):
        self.blit(self.animation_frames[self.current_frame_index], (0, 0))
    
    def draw(self, rect: Rect):
        self.fill((0, 0, 0, 0)) # Fill with transparent black
        self.draw_frame()
        self.screen.blit(self, rect)

