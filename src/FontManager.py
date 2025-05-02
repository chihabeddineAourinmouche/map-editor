from .utility import *
from .Logger import Logger
import pygame
import os

class FontManager:
    _instance = None
    _loaded_font = None
    _font_path = None
    _default_font_family = "Arial" # Default system font family
    _default_font_size = 24 # Default size for the base font object if needed, though get_font handles size

    def __new__(cls, font_path=None, default_font_family="Arial"):
        """
        Implement the singleton pattern.
        Creates a single instance of FontManager.
        """
        if cls._instance is None:
            cls._instance = super(FontManager, cls).__new__(cls)
            cls._font_path = font_path
            cls._default_font_family = default_font_family
            cls._load_font() # Load the font upon first instance creation
        return cls._instance

    @classmethod
    def _load_font(cls):
        """
        Attempts to load the font from the specified path.
        Falls back to a system font if loading fails.
        """
        if cls._font_path and os.path.exists(cls._font_path):
            try:
                # Load the font file. We load it at a base size,
                # but the get_font method will create new Font objects
                # for specific sizes as needed. Loading at a small size
                # initially is just to check if the file is valid.
                cls._loaded_font = pygame.font.Font(cls._font_path, cls._default_font_size)
                Logger.success(f"Successfully loaded font from: {cls._font_path}")
            except pygame.error as e:
                Logger.error(f"Failed to load font from {cls._font_path}: {e}")
                Logger.error(f"Falling back to system font: {cls._default_font_family}")
                cls._loaded_font = pygame.font.SysFont(cls._default_font_family, cls._default_font_size)
        else:
            Logger.info(f"Font file not found at {cls._font_path}. Falling back to system font: {cls._default_font_family}")
            cls._loaded_font = pygame.font.SysFont(cls._default_font_family, cls._default_font_size)

        # Store a cache for font objects by size for efficiency
        cls._font_cache = {}
        if cls._loaded_font:
             # Cache the default size font initially
             cls._font_cache[cls._default_font_size] = cls._loaded_font


    def get_font(self, size=None, color=(0, 0, 0), text=""):
        """
        Returns a rendered text surface using the loaded font.

        Args:
            size (int): The desired font size. If None, uses the default size.
            color (tuple): The RGB color of the text (e.g., (255, 255, 255) for white).
            text (str): The text string to render.

        Returns:
            pygame.Surface: A surface containing the rendered text, or None if font not loaded.
        """
        if not self._loaded_font:
            Logger.error("Font not loaded. Cannot render text.")
            return None

        # Use default size if none is specified
        actual_size = size if size is not None else self._default_font_size

        # Get the font object for the specific size from cache or create a new one
        if actual_size not in self._font_cache:
            try:
                if self._font_path and os.path.exists(self._font_path):
                     # Create a new Font object with the specific size from the file
                     font_for_size = pygame.font.Font(self._font_path, actual_size)
                else:
                     # Create a new SysFont object with the specific size
                     font_for_size = pygame.font.SysFont(self._default_font_family, actual_size)

                self._font_cache[actual_size] = font_for_size
            except pygame.error as e:
                 Logger.error(f"Error creating font for size {actual_size}: {e}")
                 # Fallback to the default size font if creating the specific size fails
                 if self._default_font_size in self._font_cache:
                     Logger.info(f"Using default font size {self._default_font_size} instead.")
                     font_for_size = self._font_cache[self._default_font_size]
                 else:
                     Logger.error("Default font size not available either. Cannot render text.")
                     return None # Cannot render if even default size fails


        font_to_use = self._font_cache.get(actual_size)

        if font_to_use:
            # Render the text
            text_surface = font_to_use.render(text, True, color)
            return text_surface
        else:
             Logger.error(f"Could not get font for size {actual_size}. Cannot render text.")
             return None
