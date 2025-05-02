from customtkinter import CTkFrame, CTkButton

class SplitButton(CTkFrame):
    def __init__(self, master, left_label="Left", right_label="Right", left_button_command=None, right_button_command=None, **kwargs):
        super().__init__(master, **kwargs)

        self.left_label = left_label
        self.right_label = right_label

        self.left_button_command = left_button_command
        self.right_button_command = right_button_command

        # Configure grid for 2:1 width ratio
        self.grid_columnconfigure(0, weight=2) # Left button column
        self.grid_columnconfigure(1, weight=1) # Right button column
        self.grid_rowconfigure(0, weight=1) # Allow row to expand

        self.left_button = CTkButton(
            master=self,
            text=left_label,
            command=left_button_command,
        )
        self.left_button.grid(row=0, column=0, sticky="nsew")

        # Create right button with a default corner radius initially
        self.right_button = CTkButton(
            master=self,
            text=right_label,
            command=right_button_command,
            border_width=2,
            fg_color="transparent",
            hover_color="#3b8ed0",
            border_color="#3b8ed0",
        )
        self.right_button.grid(row=0, column=1, sticky="nsew")
