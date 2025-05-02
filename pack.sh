#!/bin/bash

# --- Configuration ---
APP_NAME="Map Editor"         # The desired name for the final executable
MAIN_SCRIPT="main.py"   # The main Python script to package
CONFIG_FILE="config.yml" # The configuration file to include
DOC_DIR="doc"           # Directory containing documentation to include
RESOURCES_DIR="resources" # Directory containing resources to include

# --- Directories ---
# The root directory for the final package. PyInstaller will place contents here initially.
if [-n "$1"]; then
	DISTRIBUTABLE_ROOT="Map-Editor"
else
	DISTRIBUTABLE_ROOT="$1/Map-Editor"
fi
# The intermediate directory PyInstaller creates in one-folder mode
INTERMEDIATE_DIR="$DISTRIBUTABLE_ROOT/$APP_NAME"

# --- Virtual Environment ---
VIRTUAL_ENV_DIR=".venv" # Directory for the virtual environment

# --- PyInstaller Options ---
PYINSTALLER_OPTS=(
    --noconfirm
    --onefile # Uncomment this line if you want a single executable file (disables _internal dir)
    --name "$APP_NAME"
    --distpath "$DISTRIBUTABLE_ROOT" # PyInstaller will create $DISTRIBUTABLE_ROOT/$APP_NAME here
    --add-data "$CONFIG_FILE:."
    --add-data "$RESOURCES_DIR:$RESOURCES_DIR"
    # Add other files/directories here using --add-data
)

# --- Cleanup Function ---
# Use a trap to ensure cleanup runs even if the script exits due to an error.
cleanup() {
    local exit_status=$? # Get the exit status of the last command
    echo "Cleaning up temporary files..."

    # Deactivate virtual environment if active
    # Check if deactivate function exists before calling
    # This check is important because deactivate is only available when a venv is sourced
    if command -v deactivate &> /dev/null; then
        deactivate
        echo "Virtual environment deactivated."
    fi

    # Clean PyInstaller build artifacts
    if [ -f "$APP_NAME.spec" ]; then
        echo "Removing $APP_NAME.spec..."
        rm "$APP_NAME.spec"
    fi
    if [ -d "build" ]; then
        echo "Removing build directory..."
        rm -rf "build"
    fi

    # If the script failed (exit status is not 0), remove the distributable directory
    if [ "$exit_status" -ne 0 ]; then
        echo "Packaging failed. Removing incomplete distributable directory '$DISTRIBUTABLE_ROOT'..."
        # Use the root distributable directory as PyInstaller puts everything inside it
        if [ -d "$DISTRIBUTABLE_ROOT" ]; then
            rm -rf "$DISTRIBUTABLE_ROOT"
        fi
    fi

    echo "Cleanup complete."
    # Exit with the original exit status
    exit "$exit_status"
}

# Set the trap to run the cleanup function on EXIT (normal or abnormal)
trap cleanup EXIT

# --- Script Execution ---

echo "Starting packaging process..."

# Check if the main script exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Error: Main script '$MAIN_SCRIPT' not found."
    exit 1 # Trigger trap
fi

# Check if required files/directories exist before attempting to add them or copy them
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file '$CONFIG_FILE' not found."
    exit 1 # Trigger trap
fi
if [ ! -d "$DOC_DIR" ]; then
    echo "Error: Doc directory '$DOC_DIR' not found."
    exit 1 # Trigger trap
fi
# Check for resources directory as it will be copied later
if [ ! -d "$RESOURCES_DIR" ]; then
    echo "Error: Resources directory '$RESOURCES_DIR' not found."
    exit 1 # Trigger trap
fi


# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    # Create a virtual environment if it doesn't exist
    if [ ! -d "$VIRTUAL_ENV_DIR" ]; then
        python3 -m venv "$VIRTUAL_ENV_DIR"
        # Check the exit status immediately after venv creation
        if [ $? -ne 0 ]; then
            echo "Error: Failed to create virtual environment. Ensure python3 is in your PATH and the venv module is available."
            exit 1 # Trigger trap
        fi
        echo "Virtual environment created."
    else
        echo "Virtual environment already exists."
    fi

    # Determine the correct activation script path
    ACTIVATE_SCRIPT=""
    if [ -f "$VIRTUAL_ENV_DIR/bin/activate" ]; then
        ACTIVATE_SCRIPT="$VIRTUAL_ENV_DIR/bin/activate"
    elif [ -f "$VIRTUAL_ENV_DIR/Scripts/activate" ]; then
        ACTIVATE_SCRIPT="$VIRTUAL_ENV_DIR/Scripts/activate"
    else
        echo "Error: Could not find virtual environment activation script in $VIRTUAL_ENV_DIR/bin/ or $VIRTUAL_ENV_DIR/Scripts/."
        echo "Please check the contents of the .venv directory and your Python installation."
        exit 1 # Trigger trap
    fi

    # Activate the virtual environment
    echo "Activating virtual environment..."
    source "$ACTIVATE_SCRIPT"
    # Check the exit status immediately after activation
    if [ $? -ne 0 ]; then
         echo "Error: Failed to activate virtual environment using '$ACTIVATE_SCRIPT'."
         exit 1 # Trigger trap
    fi
    echo "Virtual environment activated."


    # Attempt to upgrade pip before installing requirements
    echo "Upgrading pip..."
    # Use the python executable from the activated environment
    python -m pip install --upgrade pip
    # Don't exit on pip upgrade failure, installation might still work
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to upgrade pip. Proceeding with requirements installation."
    fi


    # Install requirements
    # Use the pip executable from the activated environment
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install requirements."
        exit 1 # Trigger trap
    fi
    echo "Requirements installed successfully."
else
    echo "No requirements.txt found. Skipping installation."
fi

# Ensure PyInstaller is installed in the active environment
# Use the command -v check which works in activated environments
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found in the activated environment. Installing PyInstaller..."
    # Use the pip executable from the activated environment
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install PyInstaller."
        exit 1 # Trigger trap
    fi
    echo "PyInstaller installed."
else
    echo "PyInstaller found in the activated environment."
fi


# Use PyInstaller to create the executable, including specified data files
echo "Packaging the application with PyInstaller..."
# Ensure we are using the pyinstaller from the activated environment
command -v pyinstaller # Print the path to pyinstaller being used for verification
pyinstaller "${PYINSTALLER_OPTS[@]}" "$MAIN_SCRIPT"

# PyInstaller exit status is checked by the trap

# --- Post-processing: Move contents from intermediate directory to Map-Editor root ---
if [ -d "$INTERMEDIATE_DIR" ]; then
    echo "Moving contents from '$INTERMEDIATE_DIR' to '$DISTRIBUTABLE_ROOT'..."
    # Use shopt -s dotglob to include dot files/directories like _internal
    shopt -s dotglob
    mv "$INTERMEDIATE_DIR"/* "$DISTRIBUTABLE_ROOT/"
    shopt -u dotglob # Turn off dotglob
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to move contents from intermediate directory."
        # Don't exit here, packaging might still be partially successful
    fi

    # Remove the now-empty intermediate directory
    echo "Removing intermediate directory '$INTERMEDIATE_DIR'..."
    rmdir "$INTERMEDIATE_DIR" 2>/dev/null || rm -rf "$INTERMEDIATE_DIR"
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to remove intermediate directory."
    fi
else
    echo "Warning: Intermediate directory '$INTERMEDIATE_DIR' not found after PyInstaller run. Skipping post-processing."
fi

# --- Copy doc directory after packaging ---
# Check if the distributable root directory exists before copying
if [ -d "$DISTRIBUTABLE_ROOT" ]; then
    echo "Copying resources directory to '$DISTRIBUTABLE_ROOT'..."
    cp -r "$DOC_DIR" "$DISTRIBUTABLE_ROOT/"
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to copy resources directory."
        # Don't exit here, packaging might still be partially successful
    fi
else
    echo "Warning: Distributable directory '$DISTRIBUTABLE_ROOT' not found after PyInstaller run. Skipping resources copy."
fi


# The trap will handle final cleanup and exit status.
echo "Packaging process initiated. Check output for details."
# The final success message is handled by the cleanup trap if exit status is 0
