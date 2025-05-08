from math import floor
from src.utility import *
from typing import Dict
from src.ConfigUI import ConfigUI
from src.App import App
from src.Logger import Logger
import sys
from os import path
from src.FontManager import FontManager
from src.I18n import I18n

def set_config_ui_element_dimensions(config: Dict):
    config["window_width"] = max(config.get("window_width"), 600)
    config["window_height"] = max(config.get("window_height"), 400)
    
    w: int = config.get("window_width")
    h: int = config.get("window_height")
    
    drawing_area_x = 0
    drawing_area_y = 0
    drawing_area_width = floor(w * 0.85)
    drawing_area_height = h - 40

    sprite_panel_x = drawing_area_x + drawing_area_width
    sprite_panel_y = 0
    sprite_panel_width = w - drawing_area_width
    sprite_panel_height = h - 40

    display_x = 0
    display_y = drawing_area_y + drawing_area_height
    display_width = floor(w * 0.75)
    display_height = 40

    control_x = display_x + display_width
    control_y = drawing_area_y + drawing_area_height
    control_width = w - display_width
    control_height = 40
    
    config["drawing_area_x"] = drawing_area_x
    config["drawing_area_y"] = drawing_area_y
    config["drawing_area_width"] = drawing_area_width
    config["drawing_area_height"] = drawing_area_height
    config["sprite_panel_x"] = sprite_panel_x
    config["sprite_panel_y"] = sprite_panel_y
    config["sprite_panel_width"] = sprite_panel_width
    config["sprite_panel_height"] = sprite_panel_height
    config["display_x"] = display_x
    config["display_y"] = display_y
    config["display_width"] = display_width
    config["display_height"] = display_height
    config["control_x"] = control_x
    config["control_y"] = control_y
    config["control_width"] = control_width
    config["control_height"] = control_height

def set_config_language(config: Dict):
    absolute_language_file_path = path.join(os.path.normpath(config.get("language_file_directory")), config.get("language_file_name"))
    language = get_language_preference(absolute_language_file_path)
    if not language:
        language_config = ConfigUI(
            "Language",
            {
                "language": config.get("language_config_field")
            },
            "OK",
            config.get("language_config_field").get("default_value"),
            is_i18n_set=False
        ).get(field="language")
        
        config["language"] = language_config.get("language") or config.get("language")
        save_language_preference(config.get("language"), absolute_language_file_path)
    else:
        config["language"] = language

def set_user_defined_fields(configYML: Dict, config: Dict, i18n: I18n):
    ui_user_defined_fields = configYML["ui_user_definable_fields"]
    for field in ui_user_defined_fields:
        ui_user_defined_fields[field]["label"] = i18n.translate(f"app.config_ui.labels.{field}")

    config_ui: Dict = ConfigUI(
        i18n.translate("app.config_ui.window_title.initial_configuration"),
        ui_user_defined_fields,
        i18n.translate("app.config_ui.all_set"),
        i18n.translate("app.config_ui.default")
    )
    
    user_config: Dict = config_ui.get(fields=[field for field in ui_user_defined_fields])
    
    for field in ui_user_defined_fields:
        config[field] = user_config.get(field) if user_config.get(field) != None else config.get(field)
    
    save_dict_to_yaml(config, config.get("user_config_filename"))

def bundle_paths(config: Dict, bundle_dir: str):
    for field in config.get("path_fields", []):
        if config.get(field):
            p = path.join(bundle_dir, os.path.normpath(config[field]))
            config[field] = p

if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    
    bundle_dir = path.abspath(path.dirname(__file__))
    
    # Load config file
    config_file_name: str = "config.yml"
    configYML: Dict = load_yaml_to_dict(config_file_name)
    
    user_config_filename = configYML.get("user_config_filename")
    user_config = load_yaml_to_dict(user_config_filename)
    
    config: Dict = configYML
    
    """
        Choose language first
    """
    set_config_language(config)

    """
        Instantiate I18n singleton
    """
    i18n: I18n = I18n(config.get("language"), config.get("i18n"))
    
    """
        Check if there already is user_config file.
        - if so, load user config from user config file.
        - else, take user config through UI.
    """
    if not user_config:
        print("NO USER CONFIG YET")
        """
            Init configUI to request user-defined
            config and override default config.
            I define here the fields I would the
            user to be able to change through the UI.
        """
        
        set_user_defined_fields(configYML, config, i18n)
    else:
        config = user_config
    
    """
        Adjust paths for bundling
    """
    bundle_paths(config, bundle_dir)
    
    for field in config.get("theme_dependent_fields", []):
        config[field] = config[f"{field}_theme"][config.get("dark_theme", True)]
    
    set_config_ui_element_dimensions(config)
    
    FontManager(
        font_path=path.join(config.get("font_directory"), config.get("font_file_name").get(config.get("language"))),
        default_font_family=config.get("font_family")
    )
    
    if not config:
        Logger.error("Error loading configuration")
        exit(1)
        
    app = App(config)
    app.run()