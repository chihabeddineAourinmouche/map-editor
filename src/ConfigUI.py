from functools import reduce
from tkinter.filedialog import askopenfilename, askdirectory
from typing import Any, List, Optional, Union
from customtkinter import CTk, set_appearance_mode, set_default_color_theme, CTkLabel, CTkEntry, CTkButton, CTkFrame, CTkCheckBox, BooleanVar, CTkOptionMenu
from .utility import string_to_number_tuple
from .MessageBox import MessageBox
from .SplitButton import SplitButton
from .Logger import Logger
from .I18n import I18n

class ConfigUI(CTk):
    def __init__(self,
        window_title: str,
        fields_config,
        left_button_text=None,
        right_button_text=None,
        is_i18n_set=True
    ):
        super().__init__()
        
        self.i18n = None
        if is_i18n_set:
            self.i18n = I18n()
        
        self.left_button_text = left_button_text if left_button_text != None else self.i18n.translate("app.config_ui.all_set") if self.i18n else "Set"
        self.right_button_text = right_button_text if right_button_text != None else self.i18n.translate("app.config_ui.default") if self.i18n else "Cancel"
        
        self.title(window_title)
        
        height = reduce(lambda acc, cur : acc + 1, fields_config.keys(), 0) * (28 + 10 + 10) # entry-height + top-padding + bottom-padding
        
        self.geometry(f"600x{max(200, height + 28 + 20 + 20)}") # button-height + top-padding + bottom-padding
        self.resizable(False, False)

        # Use a dark theme
        set_appearance_mode("dark")
        set_default_color_theme("blue")

        self.fields_definition = fields_config  # Store the field definitions
        self.entries = {}  # Store the entry widgets using the field names as keys
        self.fields = {}  # Dictionary to store field values.
        self.labels = {} # Dictionary to store field labels.
        self.values = {}
        for key in self.fields_definition:
            self.values[key] = None
        
        # Configure column weights for resizing
        self.grid_columnconfigure(0, weight=1)  # Weight for the first button column
        self.grid_columnconfigure(1, weight=1)  # Weight for the second button column
        self.grid_rowconfigure(0, weight=1) # Allow the entry area to expand
        self.grid_rowconfigure(1, weight=1) # Allow the entry area to expand
        
        # Create a frame to hold the buttons
        entry_frame = CTkFrame(self, fg_color="transparent")
        entry_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        entry_frame.columnconfigure(1, weight=1)

        # Create labels and entry widgets for each field
        entry: CTkEntry = None
        first_entry: CTkEntry = None
        for i, (field_name, config) in enumerate(fields_config.items()):
            if config.get('type') in ("file", "directory"):
                label = CTkLabel(entry_frame, text=f"{str(config.get('label') or field_name).capitalize()}{' (*)' if config.get('required') and config.get('required') == True else ''}:")
                label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
                button: SplitButton = SplitButton(
                    master=entry_frame,
                    left_label=self.i18n.translate("app.config_ui.browse") if self.i18n else "Browse",
                    left_button_command=lambda lambda_param_field_name=field_name, lambda_param_field_type=config.get("type"), lambda_param_field_label=config.get("label") or field_name : self.open_dialog(lambda_param_field_name, lambda_param_field_label, lambda_param_field_type),
                    right_label=self.i18n.translate("app.config_ui.default") if self.i18n else "Default",
                    right_button_command=lambda lambda_param_field_name=field_name, lambda_param_default_value=config.get("default_value"): self.set_field_value(lambda_param_field_name, lambda_param_default_value)
                )
                button.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
            elif config.get("type") == "str_options":
                label = CTkLabel(entry_frame, text=f"{str(config.get('label') or field_name).capitalize()}:")
                label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
                options = config.get("options", [])
                if not options:
                    Logger.info(f"Warning: 'options' list is missing or empty for field '{field_name}' of type 'str_options'.")
                    options = [config.get("default_value")] # Provide a fallback

                option_menu = CTkOptionMenu(
                    master=entry_frame,
                    values=options,
                )
                # Set default value if provided and in options, otherwise it defaults to the first option
                if config.get("default_value") is not None and config.get("default_value") in options:
                    option_menu.set(str(config.get("default_value")))
                elif options:
                     option_menu.set(options[0]) # Set to first option if no valid default

                option_menu.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
                self.entries[field_name] = option_menu # Store the widget
            elif config.get('type') == "bool":
                checkbox_var = BooleanVar(value=config.get("default_value"))
                checkbox = CTkCheckBox(
                    master=entry_frame,
                    text=config.get("label", field_name),
                    variable=checkbox_var,
                    onvalue=1,
                    offvalue=0,
                    corner_radius=5,
                )
                # Place the checkbox in the window
                checkbox.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
                self.entries[field_name] = checkbox_var
            else:
                label = CTkLabel(entry_frame, text=f"{str(config.get('label') or field_name).capitalize()}:")
                label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
                entry = CTkEntry(entry_frame)
                entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
                self.entries[field_name] = entry  # Store the entry widget
            if i == 0 and entry:
                first_entry = entry
        
        # Create a frame to hold the buttons
        button_frame = CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=2, sticky="s")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Create the "Create" button
        create_button = CTkButton(button_frame, text=self.left_button_text, command=self.create_window)
        create_button.grid(row=0, column=0, padx=10, pady=20, sticky="ew")

        # Create the "Cancel" button
        cancel_button = CTkButton(button_frame, text=self.right_button_text, fg_color="#d8dee9", hover_color="#a8b7ce", text_color="#2e3440", command=self.destroy)
        cancel_button.grid(row=0, column=1, padx=10, pady=20, sticky="ew")

        # Give focus to the first entry when window is ready
        def on_map(event):
            if first_entry:
                first_entry.focus()
            self.unbind("<Map>") # Unbind after execution
        self.bind("<Map>", on_map)
        
        self.focus_force()  # Ensure the dialog has focus
        self.run()

    def set_field_value(self, field_name: str, value: Union[str, bool, int, float]):
        self.fields[field_name] = value
        self.values[field_name] = value

    def open_dialog(self, field_name: str, field_label: str, dialog_type: Optional[str] = "file"):
        open_function = askopenfilename
        if dialog_type == "directory":
            open_function = askdirectory
        self.values[field_name] = open_function(title=f"Pick {dialog_type} for {field_label}")

    def create_window(self):
        """
        Handles the "Create" button click event. Validates input,
        stores values in the 'fields' dictionary, and closes the dialog.
        """
        # values = {}
        for field_name, entry in self.entries.items():
            if self.values[field_name] == None:
                self.values[field_name] = entry.get()

        if not self.validate():
            return

        # Close the configuration window after successful input
        self.destroy()

    def get(self, field=None, fields=[]):
        if field:
            return {field: self.fields.get(field)}
        
        elif len(fields):
                return {key: self.fields.get(key) for key in fields}
        
        return self.fields

    def run(self):
        self.mainloop()

    def validate(self):
        for field_name, config in self.fields_definition.items():
            field_type = config.get('type')
            value = self.values[field_name]
            if not value and field_type != "bool": # Check if the user provided input
                if config.get("required") == True:
                    self.show_error_message_box(f"The field '{config.get('label') or field_name}' is required.")
                    return
                self.fields[field_name] = None
                continue
            
            if field_type == "file":
                self.fields[field_name] = value
            elif field_type == "directory":
                self.fields[field_name] = value
            elif field_type == "str_options":
                # Validation handled in validate_str_options method
                if not self.validate_str_options(config.get("label"), value, config.get("options", []), config.get("required")):
                    return False
                self.fields[field_name] = value # Store the validated string value
            elif field_type == "float":
                if not self.validate_float(field_name, value):
                    return
                else:
                    self.fields[field_name] = float(value)
            elif field_type == "int":
                if not self.validate_int(field_name, value):
                    return
                else:
                    self.fields[field_name] = int(value)
            elif field_type == "bool":
                if not self.validate_bool(field_name, value):
                    return
                else:
                    self.fields[field_name] = value
            elif field_type == "str":
                if not self.validate_str(field_name, value):
                    return
                else:
                    self.fields[field_name] = value  # Store the string value
            elif field_type == "tuple2":
                if not self.validate_tuple_of_length(field_name, value):
                    return
                else:
                    self.fields[field_name] = string_to_number_tuple(value)  # Store the validated tuple
            elif field_type == "tuple3":
                if not self.validate_tuple_of_length(field_name, value, 3):
                    return
                else:
                    self.fields[field_name] = string_to_number_tuple(value)  # Store the validated tuple
            elif field_type != "str":
                self.show_error_message_box(f"Invalid type for {str(self.fields_definition[field_name].get('label') or field_name).capitalize()}.")
                return
            else:
                self.fields[field_name] = value  # Store the string value
        return True
    
    def validate_str_options(self, field_label: str, value: Any, options: List[str], required: bool) -> bool:
        if (value is None or value == "") and not required:
            return True # Valid if not required and no selection

        if value in options:
            return True # Valid if the selected value is in the options

        # If we reach here, the value is either None/empty but required, or not in options
        if required and (value is None or value == ""):
                self.show_error_message_box(f"'{field_label.capitalize()}' is required and no option was selected.")
        else: # Value is not in options
                self.show_error_message_box(f"Invalid option selected for '{field_label.capitalize()}'.")

        return False
    
    def validate_int(self, field_name, value):
        """Validates if a value is an integer."""
        try:
            int(value)
            return True
        except ValueError:
            self.show_error_message_box(f"{str(self.fields_definition[field_name].get('label') or field_name).capitalize()} must be an integer.")
            return False

    def validate_float(self, field_name, value):
        """Validates if a value is a float."""
        try:
            float(value)
            return True
        except ValueError:
            self.show_error_message_box(f"{str(self.fields_definition[field_name].get('label') or field_name).capitalize()} must be a float.")
            return False

    def validate_str(self, field_name, value):
        """Validates if a value is a string."""
        if not isinstance(value, str):
            self.show_error_message_box(f"{str(self.fields_definition[field_name].get('label') or field_name).capitalize()} must be a string.")
            return False
        return True

    def validate_bool(self, field_name, value):
        """Validates if a value is a boolean."""
        if not isinstance(value, bool):
            self.show_error_message_box(f"{str(self.fields_definition[field_name].get('label') or field_name).capitalize()} must be a boolean.")
            return False
        return True

    def validate_tuple_of_length(self, field_name, value, length=2):
        """Validates if a value is a tuple of length 'length'"""
        v = string_to_number_tuple(value)
        if v is not None:
            if not isinstance(v, tuple) or len(v) != length:
                self.show_error_message_box(f"{str(self.fields_definition[field_name].get('label') or field_name).capitalize()} must exactly have {length} items")
                return False
        elif value:  # If string_to_tuple returns None and there was input
            self.show_error_message_box(f"Invalid tuple format for {str(self.fields_definition[field_name].get('label') or field_name).capitalize()}")
            return False
        return True
    
    def show_error_message_box(self, message):
        MessageBox(message, "error")
    
    def show_info_message_box(self, message):
        MessageBox(message)
