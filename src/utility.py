from functools import reduce
import sys
from typing import List, Optional, Tuple
import pygame
import yaml
import re
import os
from .Logger import Logger

log = print

# Custom types
Surface = pygame.Surface
Rect = pygame.Rect
Vector2 = pygame.Vector2
Font = pygame.font.Font
Event = pygame.event.Event
Coords = Tuple[int, int]
Color = Tuple[int, int, int]

class MouseButtons:
    # ANCHOR - MouseButtons
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3

class KeyboardKeys:
    # ANCHOR - KeyboardKeys
    SPACE = pygame.K_SPACE
    ESCAPE = pygame.K_ESCAPE
    LEFT_ALT = pygame.K_LALT
    LEFT_CONTROL = pygame.K_LCTRL
    Q = pygame.K_q
    S = pygame.K_s
    W = pygame.K_w
    R = pygame.K_r

def add_list(c1: List[int], c2: List[int], *c: List[int]) -> List[int]:
    """
        adds values from c2 and the rest of c
        into the values of c1
    """
    if not c1 and not c2:
        return []
    
    temp_c = list(c1)
    for i in range(len(temp_c)):
        for l in [c2, *c]:
            if len(l) > i:
                temp_c[i] += l[i]
    return list(temp_c)

def add_int(n: int, c1: Optional[List[int]] = None) -> List[int]:
  """
      adds int value to all c1 items
  """
  if not c1 or len(c1) == 0:
      return [n]
  
  temp_c = list(c1)
  for i in range(len(temp_c)):
      temp_c[i] += n
  return list(temp_c)

def multiply_int(n: int, c1: Optional[List[int]] = None) -> List[int]:
  """
      multiplies all c1 items by int value
  """
  if not c1 or len(c1) == 0:
      return []
  
  temp_c = list(c1)
  for i in range(len(temp_c)):
      temp_c[i] *= n
  return list(temp_c)

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_yaml_to_dict():
    config_file_name = "config.yml"
    config_path = get_resource_path(config_file_name)
    try:
        with open(config_path, 'r', encoding='utf8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        Logger.error(f"Error: {config_file_name} not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        Logger.error(f"Error parsing config.yml: {e}")
        return None

def save_language_preference(language, filename="temp_language.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(language)
        Logger.success(f"Language preference '{language}' saved to {filename}")
    except IOError as e:
        Logger.error(f"Error saving language preference to {filename}: {e}")

def get_language_preference(filename="temp_language.txt"):
    try:
        # Check if the file exists before trying to open it
        if not os.path.exists(filename):
                Logger.info(f"Preference file not found: {filename}")
                return None

        # Open the file in read mode ('r')
        with open(filename, "r", encoding="utf-8") as f:
            language = f.read().strip() # Read content and remove leading/trailing whitespace

        # Check if the file was empty after stripping whitespace
        if not language:
            Logger.info(f"Preference file {filename} is empty.")
            return None

        return language
    except FileNotFoundError:
        # This case is already handled by os.path.exists, but kept for robustness
        Logger.info(f"Preference file not found (in exception): {filename}")
        return None
    except IOError as e:
        Logger.info(f"Error reading language preference from {filename}: {e}")
        return None
    except Exception as e:
        Logger.info(f"An unexpected error occurred while reading {filename}: {e}")
        return None

def string_to_number_tuple(input_string):
    input_string = re.sub(r'\s{2,}', ' ', input_string).strip()
    input_string = input_string.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")
    input_string = input_string.replace(" ", "").split(",") if "," in input_string else input_string.replace(",", "").split(" ")
    if ("".join(input_string).replace(" ", "").replace(",", "").isnumeric()):
        input_string = tuple(map(lambda i : float(i), input_string))
    else:
        return None

    return input_string