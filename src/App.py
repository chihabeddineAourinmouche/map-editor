import copy
import json
import sys
import os
from typing import Dict, List, Optional, Tuple, Union
from .utility import *
from .ImageCache import ImageCache
from .SpriteData import SpriteData
from .HitBoxData import HitBoxData
from .Sprite import Sprite
from .HitBox import HitBox
from .SpritePanel import SpritePanel
from .DrawingArea import DrawingArea
from .Display import Display
from .Control import Control
from .Dialog import Dialog
from .GameManager import GameManager
from .Logger import Logger
from .ConfigUI import ConfigUI
from .I18n import I18n

class App:
    # ANCHOR[id=AppClass]
    
    def __init__(self, config: Dict[str, Union[str, int, float, bool, Dict, List, Tuple]]) -> None:
        # ANCHOR[id=AppInit]

        self.i18n: I18n = I18n()
        
        pygame.mouse.set_visible(False)
        pygame.display.set_caption(self.i18n.translate("app.window_title"))
        
        self.game_runner = GameManager(
            config.get("game_runner_game_executable_path")
        )
        
        self.map_output_file = os.path.join(config.get("map_output_directory"), config.get("map_output_filename"))
        
        self.data_type_key_dict = {
            "sprite": "sprites",
            "hitbox": "hitboxes"
        }
        self.last_saved_map_data: Dict[
            str, Tuple[Union[Tuple[int, ...], Dict[str, Union[str, Tuple[int, ...]]]]]
        ] = {"sprites": [], "hitboxes": []}
        self.map_data: Dict[
            str, Tuple[Union[Tuple[int, ...], Dict[str, Union[str, Tuple[int, ...]]]]]
        ] = {"sprites": [], "hitboxes": []}

        self.screen_width: int = config.get("window_width")
        self.screen_height: int = config.get("window_height")

        self.screen: Surface = pygame.display.set_mode((self.screen_width, self.screen_height))

        self.sprite_dir: str = config.get("sprite_directory")
        self.icon_dir: str = config.get("icon_directory")
        self.image_cache: ImageCache = ImageCache([self.sprite_dir, self.icon_dir])
        
        HitBox.color = config.get("hitbox_color")

        Sprite.selection_color = config.get("sprite_selection_color")
        
        DrawingArea.icon_size = config.get("drawing_area_icon_size")
        self.drawing_area: DrawingArea = DrawingArea(
            config.get("drawing_area_x"),
            config.get("drawing_area_y"),
            config.get("drawing_area_width"),
            config.get("drawing_area_height"),
            self.screen,
            config.get("drawing_area_canvas_width"),
            config.get("drawing_area_canvas_height"),
            config.get("drawing_area_canvas_fill_color"),
            config.get("drawing_area_preview_hit_box_outline_color"),
            config.get("drawing_area_delete_selection_outline_color"),
            config.get("drawing_area_preview_hit_box_outline_width"),
            config.get("drawing_area_delete_selection_outline_width"),
            config.get("drawing_area_canvas_grid_cell_size"),
            config.get("drawing_area_canvas_grid_color"),
            config.get("drawing_area_snap_threshold"),
            config.get("drawing_area_delete_highlight_color"),
            config.get("drawing_area_scrolling_speed"),
            config.get("drawing_area_icon_player_position")
        )
        
        self.sprite_panel: SpritePanel = SpritePanel(
            config.get("sprite_panel_x"), config.get("sprite_panel_y"),
            config.get("sprite_panel_width"), config.get("sprite_panel_height"),
            self.screen,
            self.sprite_dir,
            config.get("sprite_panel_fill_color"),
            config.get("sprite_panel_padding"),
            config.get("sprite_panel_scroll_speed")
        )
        
        self.modes = config.get("modes")
        self.sprite_mode_index, self.hitbox_mode_index, self.delete_mode_index, self.player_mode_index = range(len(self.modes))
        self.mode = self.sprite_mode_index if len(self.sprite_panel.get_sprites()) else self.hitbox_mode_index
        
        self.display_cursor_pointer = config.get("display_cursor_icon_src")
        self.display_cursor_pointer_danger = config.get("display_cursor_danger_icon_src")
        self.display_cursor_panning = config.get("display_panning_icon_src")
        
        self.display_mode_cursor_icon_delete = config.get("display_mode_cursor_icon_delete")
        self.display_mode_cursor_icon_sprite = config.get("display_mode_cursor_icon_sprite")
        self.display_mode_cursor_icon_hitbox = config.get("display_mode_cursor_icon_hitbox")
        
        self.display_game_file_not_exists = config.get("display_game_file_not_exists")
        self.display_game_file_exists = config.get("display_game_file_exists")
        
        self.display_mode_icon_files = list(map(lambda mode : f"display_{mode}.png", self.modes))
        
        self.display: Display = Display(
            config.get("display_x"),
            config.get("display_y"),
            config.get("display_width"),
            config.get("display_height"),
            self.screen,
            config.get("display_icon_size"),
            config.get("display_cursor_size"),
            [
                self.display_mode_cursor_icon_delete,
                self.display_mode_cursor_icon_sprite,
                self.display_mode_cursor_icon_hitbox,
            ],
            [
                self.display_cursor_pointer,
                self.display_cursor_pointer_danger,
                self.display_cursor_panning,
            ],
            config.get("display_font_size"),
            config.get("font_color"),
            config.get("display_tooltip_padding"),
            self.set_tooltip_text,
            config.get("display_fill_color"),
            config.get("display_icon_fill_color")
        )

        self.control : Control = Control(
            config.get("control_x"),
            config.get("control_y"),
            config.get("control_width"),
            config.get("control_height"),
            self.screen,
            config.get("control_icon_size"),
            {
                "control_save": {
                    "callback": self.save_map_data,
                    "animated_frame_suffixes": [*range(12), 0]
                },
                "control_load": {
                    "callback": self.request_load_map_data,
                    "animated_frame_suffixes": [*range(5), 0]
                },
                "control_delete": {
                    "callback": self.set_delete_mode,
                    "animated_frame_suffixes": [*range(8), 0]
                },
                "control_run": {
                    "callback": self.run_game,
                    "animated_frame_suffixes": [*range(6), 0]
                },
                "control_stop": {
                    "callback": self.game_runner.close_game,
                    "animated_frame_suffixes": [*range(7), 0]
                },
                "control_game_file": {
                    "callback": self.browse_game_executable_file,
                    "animated_frame_suffixes": [*range(10), 0]
                },
                "control_player": {
                    "callback": self.set_player_mode,
                    "animated_frame_suffixes": [*range(5), 0]
                },
            },
            self.set_tooltip_text,
            config.get("control_fill_color"),
            config.get("control_button_fill_color")
        )
        
        Dialog.overlay_fill_color = config.get("dialog_overlay_fill_color")
        Dialog.box_fill_color = config.get("dialog_box_fill_color")
        Dialog.max_box_width = config.get("dialog_max_box_width")
        Dialog.max_box_height = config.get("dialog_max_box_height")
        Dialog.font_color = config.get("font_color")
        Dialog.font_size = config.get("dialog_font_size")
        Dialog.font_family = config.get("font_family")
        Dialog.button_width = config.get("dialog_button_width") 
        Dialog.button_height = config.get("dialog_button_height")
        Dialog.box_padding_pct = config.get("dialog_box_padding_pct")
        Dialog.inter_button_gap = config.get("dialog_inter_button_gap")
        Dialog.min_message_top_padding = config.get("dialog_min_message_top_padding")
        Dialog.min_button_bottom_padding = config.get("dialog_min_button_bottom_padding")
        self.dialog: Dialog = None
        self.dialog_close_callback = self.close_dialog
        
        self.run_game_requested = False
        

        self.modifier_key_CTRL_pressed = False
        
        self.tooltip_text = None

        self.running: bool = True



    # ANCHOR[id=GameManagement]
    def browse_game_executable_file_and_close_dialog(self):
        self.close_dialog()
        self.browse_game_executable_file()
        
    def browse_game_executable_file(self):
        pygame.mouse.set_visible(True)
        browsing_ui_fields: Dict = {
            "game_runner_game_executable_path": {
                "label": self.i18n.translate("app.config_ui.game_executable_path_label"),
                "type": "file",
                "default_value": self.game_runner.get_game_executable_path(),
                "required": True,
            }
        }
        browsing_ui: ConfigUI = ConfigUI(
            self.i18n.translate("app.config_ui.window_title.browse_game_executable_file"),
            browsing_ui_fields, self.i18n.translate("app.config_ui.set_button"),
            self.i18n.translate("app.config_ui.cancel_button")
        )
        pygame.mouse.set_visible(False)
        field_key_value: str = browsing_ui.get(field="game_runner_game_executable_path")
        game_runner_game_executable_path = field_key_value.get("game_runner_game_executable_path")
        self.game_runner.set_game_executable_path(game_runner_game_executable_path)
    
    def run_game(self):
        if not self.game_runner.get_game_executable_path():
            self.set_dialog(Dialog(
                self.screen,
                self.i18n.translate("app.dialogs.no_game_specified.message"),
                {
                    self.i18n.translate("app.dialogs.no_game_specified.add_game_button"): {
                        "callback": self.browse_game_executable_file_and_close_dialog,
                        "filled": True
                    },
                    self.i18n.translate("app.dialogs.no_game_specified.back_button"): {
                        "callback": self.close_dialog,
                        "filled": False
                    }
                }
            ))
        elif not self.check_pristine():
            self.set_dialog(Dialog(
                self.screen,
                self.i18n.translate("app.dialogs.unsaved_changes_run.message"),
                {
                   self.i18n.translate( "app.dialogs.unsaved_changes_run.just_run_button"): {
                        "callback": self.request_run_game,
                        "filled": False
                    },
                   self.i18n.translate ("app.dialogs.unsaved_changes_run.save_first_button"): {
                        "callback": self.save_map_data_and_run_game,
                        "filled": True
                    }
                }
            ))
        else:
            self.execute_run_game()

    def save_map_data_and_run_game(self):
        self.save_map_data()
        self.execute_run_game()

    def set_dialog(self, dialog: Optional[Dialog] = None):
        self.dialog = dialog

    def request_run_game(self):
        """Sets a flag to run the game after the dialog is closed."""
        self.set_dialog()  # Close the dialog dialog
        self.run_game_requested = True

    def execute_run_game(self):
        self.game_runner.run_game()

    def close_dialog(self):
        self.set_dialog()
        self.run_game_requested = False


    # ANCHOR[id=ModeManagement]
    def set_mode(self, md: Optional[int] = None) -> None:
        if md == None:
            self.mode = (self.mode + 1) % len(self.modes)
        else:
            self.mode = md
    
    def is_sprite_mode(self):
        return self.mode == self.sprite_mode_index
    
    def is_hitbox_mode(self):
        return self.mode == self.hitbox_mode_index
    
    def is_delete_mode(self):
        return self.mode == self.delete_mode_index

    def is_player_mode(self):
        return self.mode == self.player_mode_index
    
    def get_mode(self):
        return self.modes[self.mode]

    def set_sprite_mode(self):
        if len(self.sprite_panel.get_sprites()):
            self.set_mode(self.sprite_mode_index)
        else:
            self.switch_mode()
    
    def set_delete_mode(self):
        self.set_mode(self.delete_mode_index)
    
    def set_player_mode(self):
        self.set_mode(self.player_mode_index)
    
    def switch_mode(self):
        if not self.drawing_area.get_is_drawing_hitbox():
            self.set_mode()
            if self.is_delete_mode() and (not len(self.map_data["sprites"]) and not len(self.map_data["hitboxes"])):
                self.set_mode()
            if self.is_sprite_mode() and not len(self.sprite_panel.get_sprites()):
                self.set_mode()



    # ANCHOR[id=AppClosing]
    def quit(self):
        pygame.quit()
        sys.exit()
    
    def save_map_data_and_quit(self):
        self.save_map_data()
        self.stop_running()
    
    def close_without_saving(self):
        self.stop_running()
    
    def stop_running(self):
        self.set_dialog()
        self.running = False

    def close(self) -> None:
        if not self.check_pristine():
            self.set_dialog(Dialog(
                self.screen,
                self.i18n.translate("app.dialogs.unsaved_changes_quit.message"),
                {
                    self.i18n.translate("app.dialogs.unsaved_changes_quit.just_quit_button"): {
                        "callback": self.close_without_saving,
                        "filled": False
                    },
                    self.i18n.translate("app.dialogs.unsaved_changes_quit.save_first_button"): {
                        "callback": self.save_map_data_and_quit,
                        "filled": True
                    }
                }
            ))
        else:
            self.stop_running()



    # ANCHOR[id=DataManagement]
    def check_pristine(self):
        return self.map_data == self.last_saved_map_data

    def add_data(self, data: Union[SpriteData, HitBoxData], data_type: str):
        self.map_data[self.data_type_key_dict[data_type]].append(data)
    
    def delete_data(self, _id: str, data_type: str) -> None:
        self.map_data[self.data_type_key_dict[data_type]] = list(filter(lambda d : d["id"] != _id, self.map_data[self.data_type_key_dict[data_type]]))
        if self.drawing_area.is_empty() and self.is_delete_mode():
            self.switch_mode()
    
    def set_player_position(self, player_pos: Coords) -> None:
        self.map_data["starting_position"] = player_pos

    def save_map_data(self):
        try:
            with open(self.map_output_file, "w") as f:
                json.dump(self.map_data, f, indent=4)
            self.last_saved_map_data = copy.deepcopy(self.map_data)
        except IOError as e:
            Logger.error(f"Error saving map data to JSON file")

    def browse_map_data_file(self) -> str:
        pygame.mouse.set_visible(True)
        browsing_ui_fields: Dict = {
            "map_data_file_path": {
                "label": self.i18n.translate("app.config_ui.labels.map_data_file_path"),
                "type": "file",
                "required": True,
            }
        }
        browsing_ui: ConfigUI = ConfigUI(
            self.i18n.translate("app.config_ui.window_title.browse_map_data_file_path"),
            browsing_ui_fields, self.i18n.translate("app.config_ui.set_button"),
            self.i18n.translate("app.config_ui.cancel_button")
        )
        pygame.mouse.set_visible(False)
        field_key_value: str = browsing_ui.get(field="map_data_file_path")
        map_data_file_path = field_key_value.get("map_data_file_path")
        return map_data_file_path

    def load_map_data(self):
        self.close_dialog()
        map_data_file_path: str = self.browse_map_data_file()
        if map_data_file_path != None:
            data: Dict = load_json_to_dict(map_data_file_path)
            if all(map(lambda d : self.sprite_panel.has_sprite_with_name(d["file_name"]), data["sprites"])):
                if not data.get("sprites"):
                    data["sprites"] = []
                if not data.get("hitboxes"):
                    data["hitboxes"] = []
                if not data.get("starting_position"):
                    data["starting_position"] = None
                if data != None:
                    self.drawing_area.load_data(data)
                    self.map_data = copy.deepcopy(data)
            else:
                self.set_dialog(Dialog(
                    self.screen,
                    self.i18n.translate("app.dialogs.map_data_sprite_mismatch.message"),
                    {
                        self.i18n.translate("app.dialogs.map_data_sprite_mismatch.cancel"): {
                            "callback": self.close_dialog,
                            "filled": False
                        },
                        self.i18n.translate("app.dialogs.map_data_sprite_mismatch.load_another"): {
                            "callback": self.request_load_map_data,
                            "filled": True
                        }
                    }
                ))

    def save_map_data_then_load_new_map_data(self):
        self.save_map_data()
        self.load_map_data()

    def request_load_map_data(self):
        if not self.drawing_area.is_empty() or not self.check_pristine():
            self.set_dialog(Dialog(
                self.screen,
                self.i18n.translate("app.dialogs.current_design_will_be_replaced.message"),
                {
                    self.i18n.translate("app.dialogs.current_design_will_be_replaced.just_load"): {
                        "callback": self.load_map_data,
                        "filled": False
                    },
                    self.i18n.translate("app.dialogs.current_design_will_be_replaced.save_first"): {
                        "callback": self.save_map_data_then_load_new_map_data,
                        "filled": True
                    }
                }
            ))
        else:
            self.load_map_data()

    # ANCHOR[id=Tooltip]
    def set_tooltip_text(self, text: Optional[str] = None) -> None:
        self.tooltip_text = text
    
    
    
    # ANCHOR[id=ControlManagement]
    def get_control_button_update_data(self) -> Dict[str, Dict[str, Union[str, bool]]]:
        return {
            "control_save": {
                "disabled": self.check_pristine(),
                "hint": {
                    "disabled": self.i18n.translate("app.controls.save.hint_disabled"),
                    "enabled": self.i18n.translate("app.controls.save.hint_enabled"),
                },
            },
            "control_load": {
                "disabled": False,
                "hint": {
                    "disabled": None,
                    "enabled": self.i18n.translate("app.controls.load.hint_enabled"),
                },
            },
            "control_delete": {
                "disabled": self.drawing_area.is_empty() or self.is_delete_mode(),
                "hint": {
                    "disabled": self.i18n.translate("app.controls.delete.hint_disabled_already_in_mode") if self.is_delete_mode() else self.i18n.translate("app.controls.delete.hint_disabled_no_objects"),
                    "enabled": self.i18n.translate("app.controls.delete.hint_enabled"),
                },
            },
            "control_run": {
                "disabled": self.drawing_area.is_empty() or self.game_runner.get_is_running(),
                "hint": {
                    "disabled": self.i18n.translate("app.controls.run.hint_disabled_running") if self.game_runner.get_is_running() else self.i18n.translate("app.controls.run.hint_disabled_no_objects"),
                    "enabled": self.i18n.translate("app.controls.run.hint_enabled"),
                },
            },
            "control_stop": {
                "disabled": not self.game_runner.get_is_running(),
                "hint": {
                    "disabled": self.i18n.translate("app.controls.stop.hint_disabled"),
                    "enabled": self.i18n.translate("app.controls.stop.hint_enabled"),
                },
            },
            "control_game_file": {
                "disabled": False,
                "hint": {
                    "disabled": self.i18n.translate("app.controls.game_file.hint_disabled"),
                    "enabled": self.i18n.translate("app.controls.game_file.hint_enabled"),
                },
            },
            "control_player": {
                "disabled": False,
                "hint": {
                    "disabled": None,
                    "enabled": self.i18n.translate("app.controls.player.hint_enabled"),
                },
            },
        }


    # ANCHOR[id=DisplayManagement]
    def get_display_data(self):
        return [
            {
                "type": "icon",
                "icon_name": self.display_game_file_not_exists if not self.game_runner.get_game_executable_path() else self.display_game_file_exists,
                "hint": self.i18n.translate("app.display.game_file_status_no_game") if not self.game_runner.get_game_executable_path() else self.i18n.translate("app.display.game_file_status_game_loaded"),
            },
            {
                "type": "icon",
                "icon_name": self.display_mode_icon_files[self.mode],
                "hint": self.i18n.translate(f"app.display.mode_{self.modes[self.mode]}"),
            },
            {
                "type": "text",
                "data": self.i18n.translate(f"app.display.mode_{self.modes[self.mode]}"),
                "hint": self.i18n.translate(f"app.display.mode_{self.modes[self.mode]}_hint"),
            },
            {
                "type": "text",
                "data": str(self.drawing_area.get_mouse_position_on_canvas()),
                "hint": "x, y",
            },
        ]



    # ANCHOR[id=MainLoop]
    def update(self) -> None:
        
        for event in pygame.event.get():
            self.set_tooltip_text()
            
            if self.dialog:
                # LINK: #DialogUpdate
                self.dialog.update(
                    event,
                    self.dialog_close_callback
                )
            else:
                # ANCHOR[id=AppUpdate]
                # LINK: #SpritePanelUpdate
                self.sprite_panel.update(event, self.set_sprite_mode, self.switch_mode)
                
                # LINK: #DrawingAreaUpdate
                self.drawing_area.update(event,
                    self.is_sprite_mode(),
                    self.is_hitbox_mode(),
                    self.is_delete_mode(),
                    self.is_player_mode(),
                    self.sprite_panel.get_sprites(),
                    self.sprite_panel.get_selected_sprite_id(),
                    self.switch_mode,
                    self.add_data,
                    self.delete_data,
                    self.set_player_position
                )
                
                # LINK: #ControlUpdate
                self.control.update(
                    event,
                    self.get_control_button_update_data()
                )
                
            # LINK: #DisplayUpdate
            self.display.update(
                event,
                {
                    "cursor": self.display_cursor_panning if self.drawing_area.get_is_panning()
                        else self.display_cursor_pointer_danger if self.is_delete_mode() 
                            and self.drawing_area.get_is_hovered()
                            and not self.dialog
                        else self.display_cursor_pointer,
                },
                self.get_display_data(),
                self.tooltip_text
            )
            
            if self.run_game_requested and not self.dialog: # Check if requested AND dialog is closed
                self.execute_run_game()
                self.run_game_requested = False
            
            if event.type == pygame.QUIT:
                self.close()
            
            if event.type == pygame.KEYDOWN:
                if event.key == KeyboardKeys.LEFT_CONTROL:
                    self.modifier_key_CTRL_pressed = True
            
            if event.type == pygame.KEYUP:
                if event.key == KeyboardKeys.LEFT_CONTROL:
                    self.modifier_key_CTRL_pressed = False
                
                # CTRL MODIFIED INPUT
                if self.modifier_key_CTRL_pressed:
                    if event.key == KeyboardKeys.S:
                        self.save_map_data()
                    elif event.key == KeyboardKeys.W or event.key == KeyboardKeys.Q:
                        self.close()
                    elif event.key == KeyboardKeys.R:
                        if (not self.drawing_area.is_empty()) and (not self.game_runner.get_is_running()):
                            self.run_game()
                    elif event.key == KeyboardKeys.L:
                        self.request_load_map_data()
            
                    # TODO[id=DEBUG]
                    elif event.key == KeyboardKeys.SPACE:
                        self.stop_running()

                # FIXME - Keeping this for DEBUG
                if event.key == KeyboardKeys.SPACE:
                    pass
    
    def fixed_update(self):
        # ANCHOR[id=AppFixedUpdate]
        self.drawing_area.fixed_update()
        self.control.fixed_update(self.get_control_button_update_data())

    def draw(self) -> None:
        # ANCHOR[id=AppDraw]
        # LINK: #DrawingAreaDraw
        self.drawing_area.draw()
        
        # LINK: #SpritePanelDraw
        self.sprite_panel.draw()

        # LINK: #ControlDraw
        self.control.draw()
            
        # LINK: #DisplayDraw
        self.display.draw()
        
        if self.dialog:
            # LINK: #DialogDraw
            self.dialog.draw()
        
        # Always draw display cursor on top of display tooltip and draw both on top of all other elements
        if self.tooltip_text:
            self.display.draw_tooltip()
        self.display.draw_cursor()

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.fixed_update()
            self.update()
            self.draw()
        self.quit()


# LINK #AppClass
# LINK #AppInit
# LINK #GameRun
# LINK #ModeManagement
# LINK #AppClosing
# LINK #DataManagement
# LINK #MainLoop
# LINK #AppUpdate
# LINK #AppFixedUpdate
# LINK #AppDraw

# FIXME
# LINK #DEBUG
