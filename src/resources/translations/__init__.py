"""
Translation Management for Projector Control Application

Provides centralized translation management with support for English and Hebrew.
Implements caching and fallback mechanisms for robust i18n support.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TranslationManager:
    """
    Manages application translations with caching and fallback support.

    Supports dynamic language switching and provides a simple key-based
    translation lookup system. Defaults to English if a key is missing
    in the selected language.

    Attributes:
        current_language: Currently active language code (e.g., "en", "he")
    """

    SUPPORTED_LANGUAGES = ["en", "he"]
    DEFAULT_LANGUAGE = "en"

    def __init__(self, language: str = "en"):
        """
        Initialize the TranslationManager.

        Args:
            language: Initial language code. Defaults to "en".
                     Falls back to "en" if the specified language is not available.
        """
        self._current_language = self.DEFAULT_LANGUAGE
        self._translations: Dict[str, Dict[str, str]] = {}
        self._translations_dir = Path(__file__).parent

        # Preload all available languages
        self._load_all_languages()

        # Set the requested language (will validate and fallback if needed)
        self.set_language(language)

    def _load_all_languages(self) -> None:
        """Preload all supported language files into cache."""
        for lang_code in self.SUPPORTED_LANGUAGES:
            lang_file = self._translations_dir / f"{lang_code}.json"

            if not lang_file.exists():
                logger.warning(f"Translation file not found: {lang_file}")
                continue

            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self._translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for language: {lang_code}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {lang_file}: {e}")
                self._translations[lang_code] = {}
            except Exception as e:
                logger.error(f"Failed to load {lang_file}: {e}")
                self._translations[lang_code] = {}

    def set_language(self, language: str) -> bool:
        """
        Switch to a different language.

        Args:
            language: Language code to switch to (e.g., "en", "he")

        Returns:
            True if the language was successfully set, False if it fell back to default
        """
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(
                f"Unsupported language '{language}', falling back to '{self.DEFAULT_LANGUAGE}'"
            )
            self._current_language = self.DEFAULT_LANGUAGE
            return False

        if language not in self._translations or not self._translations[language]:
            logger.warning(
                f"No translations loaded for '{language}', falling back to '{self.DEFAULT_LANGUAGE}'"
            )
            self._current_language = self.DEFAULT_LANGUAGE
            return False

        self._current_language = language
        logger.info(f"Language set to: {language}")
        return True

    def _get_nested_value(self, data: dict, key: str) -> Optional[str]:
        """
        Get a value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            key: Dot-notation key (e.g., "app.name", "wizard.title")

        Returns:
            Value if found, None otherwise
        """
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current if isinstance(current, str) else None

    def get(self, key: str, default: str = "") -> str:
        """
        Get a translated string for the given key.

        Falls back to English if the key is not found in the current language.
        Falls back to the provided default if the key is not found in any language.

        Args:
            key: Translation key (e.g., "app.name", "wizard.title")
            default: Default string to return if key is not found

        Returns:
            Translated string, English fallback, or default value
        """
        # Try current language
        current_translations = self._translations.get(self._current_language, {})
        value = self._get_nested_value(current_translations, key)
        if value is not None:
            return value

        # Fallback to English if not in current language
        if self._current_language != self.DEFAULT_LANGUAGE:
            english_translations = self._translations.get(self.DEFAULT_LANGUAGE, {})
            value = self._get_nested_value(english_translations, key)
            if value is not None:
                logger.debug(
                    f"Key '{key}' not found in '{self._current_language}', "
                    f"using English fallback"
                )
                return value

        # No translation found
        logger.warning(f"Translation key not found: '{key}'")
        return default if default else f"[{key}]"

    @property
    def current_language(self) -> str:
        """Get the currently active language code."""
        return self._current_language

    def available_languages(self) -> list:
        """
        Get list of available language codes.

        Returns:
            List of language codes that have loaded translations
        """
        return [
            lang for lang in self.SUPPORTED_LANGUAGES
            if lang in self._translations and self._translations[lang]
        ]

    def is_rtl(self) -> bool:
        """
        Check if the current language is right-to-left.

        Returns:
            True if current language is Hebrew (RTL), False otherwise
        """
        return self._current_language == "he"

    def reload(self) -> None:
        """Reload all translation files from disk (useful for development)."""
        logger.info("Reloading all translations")
        self._translations.clear()
        self._load_all_languages()


# Global translation manager instance
_manager: Optional[TranslationManager] = None


def get_translation_manager(language: str = "en") -> TranslationManager:
    """
    Get the global TranslationManager instance.

    Creates a new instance on first call. Subsequent calls return the same instance.

    Args:
        language: Initial language (only used on first call)

    Returns:
        Global TranslationManager instance
    """
    global _manager
    if _manager is None:
        _manager = TranslationManager(language)
    return _manager


def t(key: str, default: str = "") -> str:
    """
    Convenience function for translation lookup.

    Args:
        key: Translation key
        default: Default value if key not found

    Returns:
        Translated string
    """
    return get_translation_manager().get(key, default)
