import subprocess
import signal
import os
import platform
import sys
from typing import Union
from .utility import *
from .Logger import Logger

class GameManager:
    def __init__(self, game_executable_path: Optional[str] = None):
        self.game_executable_path: str = game_executable_path
        self.is_running = False
        self.process = None  # To store the subprocess object

    # ANCHOR[id=Getters]
    def get_is_running(self):
        if self.process:
            return self.process.poll() is None  # Check if the process is still running
        return self.is_running

    def get_game_executable_path(self) -> Union[str, None]:
        return self.game_executable_path

    # ANCHOR[id=Getters]
    def set_game_executable_path(self, game_executable_path: str) -> None:
        self.game_executable_path = game_executable_path

    def run_game(self):
        self.is_running = True
        try:
            kwargs = {}
            if platform.system() != 'Windows':
                kwargs['preexec_fn'] = os.setsid  # Only for POSIX

            self.process = subprocess.Popen(
                [self.game_executable_path],# command,
                cwd=os.path.dirname(self.game_executable_path),
                #stdout=subprocess.PIPE,
                #stderr=subprocess.PIPE,
                shell=False # Recommended for security
            )
            Logger.info(f"Game process started")
        except Exception as e:
            Logger.error(f"Error starting game process: {e}")
            self.is_running = False
            self.process = None

    def close_game(self):
        if self.process:
            Logger.info(f"Closing game process")
            try:
                if platform.system() != 'Windows':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)  # Send SIGTERM to the process group (POSIX)
                    self.process.wait(timeout=5)
                    if self.process.poll() is None:
                        Logger.info("Game process did not terminate gracefully.")
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                        self.process.wait()
                else:
                    self.process.terminate()  # Use terminate() on Windows
                    self.process.wait(timeout=5)
                    if self.process.poll() is None:
                        Logger.info("Game process did not terminate gracefully.")
                        self.process.kill()
                        self.process.wait()
            except ProcessLookupError:
                Logger.error("Game process not found.")
            except Exception as e:
                Logger.error(f"Error closing game process: {e}")
            finally:
                self.process = None
                self.is_running = False
        else:
            Logger.info("No game process is currently running.")
