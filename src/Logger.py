import textwrap
import shutil # To get terminal size
import os # To handle file operations
from abc import ABC # Import Abstract Base Class

log = print

class Logger(ABC):
    """
    An abstract base class for logging with console (table) and file capabilities.
    Provides class methods for different log levels.
    """
    _log_file: str = "logs.log"

    @classmethod
    def _log(cls, level: str, *args, **kwargs):
        """
        Internal class method to handle the core logging logic (console and file).

        Args:
            level (str): The log level (e.g., "INFO", "ERROR", "SUCCESS").
            *args: Variable length argument list for the message content.
            **kwargs: Arbitrary keyword arguments (passed to print, e.g., sep, end).
        """
        # Combine args into a single message string for both console and file
        message = " ".join(map(str, args))

        # --- Console Logging (Table Format) ---
        # Get terminal width, default to a reasonable size if not available
        try:
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80 # Default width

        # Define column widths (Level | Message)
        # We reserve some space for borders and padding
        level_col_width = 10 # Fixed width for the level column
        message_col_width = terminal_width - level_col_width - 5 # Adjust for borders and padding

        # Ensure message column is not too small
        if message_col_width < 10:
            message_col_width = 10 # Minimum width

        # Wrap the message text for console output
        wrapped_message_lines = textwrap.wrap(message, width=message_col_width)

        # Determine the height of the table (number of lines in the message)
        table_height = max(1, len(wrapped_message_lines)) # At least one line

        # Define table border characters
        horizontal_border = '-'
        vertical_border = '|'
        corner = '+'
        padding = ' '

        # Print the top border
        log(f"{corner}{horizontal_border * (level_col_width + 2)}{corner}{horizontal_border * (message_col_width + 2)}{corner}")

        # Print the table rows
        for i in range(table_height):
            # Get the current line of the message, or empty string if no more lines
            current_message_line = wrapped_message_lines[i] if i < len(wrapped_message_lines) else ""

            # Format the level cell (only on the first line)
            if i == 0:
                level_cell = f"{padding}{level:<{level_col_width}}{padding}" # Left-align level
            else:
                level_cell = f"{padding * (level_col_width + 2)}" # Empty space for subsequent lines

            # Format the message cell
            message_cell = f"{padding}{current_message_line:<{message_col_width}}{padding}" # Left-align message

            # Print the row
            log(f"{vertical_border}{level_cell}{vertical_border}{message_cell}{vertical_border}")

        # Print the bottom border
        log(f"{corner}{horizontal_border * (level_col_width + 2)}{corner}{horizontal_border * (message_col_width + 2)}{corner}")

        # --- File Logging ---
        if cls._log_file: # Check if the class attribute log file is set
            try:
                # Open the file in append mode, create if it doesn't exist
                with open(cls._log_file, 'a') as f:
                    # Write the simple log message format
                    f.write(f"{level.upper()}: {message}\n")
            except IOError as e:
                # Log an error to the console if file writing fails
                # Use print here to avoid potential recursion or issues with the logger itself
                log(f"[ERROR] Could not write to log file {cls._log_file}: {e}")


    @classmethod
    def error(cls, *args, **kwargs):
      """
      Logs an error message using the formatted table log function
      and optionally writes to the class-defined log file.
      """
      cls._log("ERROR", *args, **kwargs)


    @classmethod
    def info(cls, *args, **kwargs):
      """
      Logs an informational message using the formatted table log function
      and optionally writes to the class-defined log file.
      """
      cls._log("INFO", *args, **kwargs)


    @classmethod
    def success(cls, *args, **kwargs):
      """
      Logs a success message using the formatted table log function
      and optionally writes to the class-defined log file.
      """
      cls._log("SUCCESS", *args, **kwargs)