from typing import Dict, Optional, Any
from .Logger import Logger

class I18n:
    """
    A singleton class for handling internationalization (i18n).

    This class loads translation dictionaries and provides a method
    to translate strings based on the current language.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """
        Implement the singleton pattern.

        Ensures that only one instance of the I18n class is created.
        """
        if cls._instance is None:
            cls._instance = super(I18n, cls).__new__(cls)
        return cls._instance

    def __init__(self, language: str = "English", translations: Optional[Dict[str, Dict[str, str]]] = None):
        """
        Initialize the I18n instance.

        This method is called only on the first instantiation of the class.

        Args:
            language: The default language code (e.g., 'English', 'Spanish'). Defaults to 'English'.
            translations: A dictionary containing translations.
                          Expected format: {'language_code': {'key': 'translated_string'}}.
                          Defaults to an empty dictionary.
        """
        if not self._initialized:
            self._language = language
            # Store the translations directly as they are passed (should be {'lang_code': {}})
            self._translations = translations if translations is not None else {}
            self._initialized = True
            Logger.info(f"I18n initialized with language: {self._language}")
        else:
            # Prevent re-initialization with different values or just ignore
            pass

    def set_language(self, language: str):
        """
        Sets the current language for translations.

        Args:
            language: The language code to set.
        """
        if language in self._translations:
            self._language = language
            Logger.info(f"Language set to: {self._language}")
        else:
            Logger.info(f"Warning: Language '{language}' not found in translations. Keeping current language: {self._language}")


    def translate(self, key: str, default: Optional[str] = None) -> str:
        """
        Translates a given key into the current language, supporting dot notation
        for nested keys.

        Args:
            key: The dot-separated key string to translate (e.g., 'app.window_title').
            default: An optional default string to return if the key or language
                     is not found. If None, the key itself is returned.

        Returns:
            The translated string, the default string if provided, or the key
            itself if no translation is found.
        """
        # Get translations for the current language
        current_level: Any = self._translations.get(self._language)

        if current_level is None:
             # Language not found
             if default is not None:
                 return default
             Logger.info(f"Warning: Language '{self._language}' not found in translations.")
             return key # Return key if language not found and no default

        # Split the key by dots to traverse the nested dictionary
        keys = key.split('.')

        # Traverse the nested dictionary
        for k in keys:
            if isinstance(current_level, dict):
                current_level = current_level.get(k)
            else:
                # A key in the path did not lead to a dictionary (intermediate key is not a dict)
                current_level = None
                break # Stop traversing

        # Check the final result of the traversal
        if current_level is not None:
            return str(current_level) # Found the translation

        # If translation not found after traversal
        if default is not None:
            return default
        else:
            Logger.error(f"Warning: Translation key '{key}' not found for language '{self._language}'.")
            return key