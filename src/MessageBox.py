from customtkinter import CTkLabel, CTkButton, CTkFont, CTkToplevel

class MessageBox(CTkToplevel):
    """
    A styled error message box using CustomTkinter.
    """
    COLORS = {
        "info": "#ebcb8b",
        "error": "#bf616a"
    }
    
    ICONS = {
        "info": "i",
        "error": "!"
    }
    
    def __init__(self, message, _type="info", **kwargs):
        super().__init__(**kwargs)
        self.type = _type
        self.title(self.type.capitalize())
        self.geometry("400x200")  # Set a reasonable default size
        self.resizable(False, False)  # Prevent resizing for a consistent look

        # Use a grid layout for better control over widget placement
        self.grid_columnconfigure(0, weight=1)  #message
        self.grid_columnconfigure(1, weight=1) #button
        self.grid_rowconfigure(0, weight=1)    #icon and message
        self.grid_rowconfigure(1, weight=1)  #button

        # Error icon (optional, you can customize this)
        #  For now, we'll use a text label as a placeholder.  A real icon would be better.
        self.icon_label = CTkLabel(self, text=self.ICONS[self.type], font=CTkFont(size=32, weight="bold"), text_color=self.COLORS[self.type])  # Use red for error
        self.icon_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 0), sticky="n") # Top Center

        # Message label
        self.message_label = CTkLabel(self, text=message, font=CTkFont(size=16), wraplength=320, justify="left")
        self.message_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(62, 0), sticky="nsew") # Middle Left

        # OK button
        self.ok_button = CTkButton(self, text="OK", command=self.destroy, font=CTkFont(size=16), width=100, height=30)
        self.ok_button.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="se") # Bottom Right
        self.ok_button.focus_set()  # Give the OK button initial focus

        # Make the dialog modal (optional, prevents interaction with other windows)
        self.grab_set()
        self.focus_force()  # Ensure the dialog has focus
        self.wait_window() #added show
