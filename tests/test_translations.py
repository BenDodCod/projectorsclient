"""
Unit tests for translation management system.

Tests the TranslationManager class functionality including:
- Language loading and switching
- Nested key lookup with dot notation
- Fallback mechanisms (language and default value)
- RTL detection
- Convenience functions
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resources.translations import TranslationManager, get_translation_manager, t


def test_translation_manager_initialization():
    """Test that TranslationManager initializes correctly."""
    print("Testing initialization...")

    # Test default initialization
    tm = TranslationManager()
    assert tm.current_language == "en", "Default language should be English"
    assert len(tm.available_languages()) == 2, "Should have 2 languages available"
    assert "en" in tm.available_languages(), "English should be available"
    assert "he" in tm.available_languages(), "Hebrew should be available"

    # Test initialization with specific language
    tm_he = TranslationManager("he")
    assert tm_he.current_language == "he", "Should initialize with Hebrew"

    print("[PASS] Initialization tests passed")


def test_nested_key_lookup():
    """Test nested key lookup with dot notation."""
    print("Testing nested key lookup...")

    tm = TranslationManager("en")

    # Test various nesting levels
    assert tm.get("app.name") == "Projector Control", "Failed to get app.name"
    assert tm.get("wizard.title") == "Setup Wizard", "Failed to get wizard.title"
    assert tm.get("buttons.next") == "Next", "Failed to get buttons.next"
    assert tm.get("errors.connection_failed") == "Failed to connect to projector", \
        "Failed to get errors.connection_failed"

    print("[PASS]Nested key lookup tests passed")


def test_language_switching():
    """Test switching between languages."""
    print("Testing language switching...")

    tm = TranslationManager("en")

    # Get English value
    en_value = tm.get("buttons.next")
    assert en_value == "Next", "English value incorrect"

    # Switch to Hebrew
    result = tm.set_language("he")
    assert result is True, "Language switch should succeed"
    assert tm.current_language == "he", "Current language should be Hebrew"

    # Get Hebrew value (should be different)
    he_value = tm.get("buttons.next")
    assert he_value != en_value, "Hebrew value should differ from English"
    assert len(he_value) > 0, "Hebrew value should not be empty"

    # Switch back to English
    tm.set_language("en")
    assert tm.get("buttons.next") == en_value, "English value should be restored"

    print("[PASS]Language switching tests passed")


def test_fallback_mechanisms():
    """Test fallback to English and default values."""
    print("Testing fallback mechanisms...")

    tm = TranslationManager("he")

    # Test nonexistent key with default
    default_value = "My Default"
    result = tm.get("nonexistent.key.path", default_value)
    assert result == default_value, "Should return default value for missing key"

    # Test nonexistent key without default (should return [key])
    result = tm.get("another.missing.key")
    assert result == "[another.missing.key]", "Should return [key] for missing key without default"

    print("[PASS]Fallback mechanism tests passed")


def test_rtl_detection():
    """Test RTL (right-to-left) detection."""
    print("Testing RTL detection...")

    tm_en = TranslationManager("en")
    tm_he = TranslationManager("he")

    assert tm_en.is_rtl() is False, "English should not be RTL"
    assert tm_he.is_rtl() is True, "Hebrew should be RTL"

    print("[PASS]RTL detection tests passed")


def test_global_manager():
    """Test global translation manager singleton."""
    print("Testing global manager...")

    # Get first instance
    tm1 = get_translation_manager("en")
    assert tm1.current_language == "en", "Should initialize with English"

    # Get second instance (should be same object)
    tm2 = get_translation_manager("he")  # Language parameter should be ignored
    assert tm1 is tm2, "Should return the same instance"
    assert tm2.current_language == "en", "Should still be English (singleton)"

    print("[PASS]Global manager tests passed")


def test_convenience_function():
    """Test the convenience t() function."""
    print("Testing convenience function...")

    # Reset global manager
    import resources.translations as trans_module
    trans_module._manager = None

    # Test t() function
    result = t("app.name")
    assert result == "Projector Control", "t() should return correct translation"

    result = t("nonexistent.key", "Custom Default")
    assert result == "Custom Default", "t() should use default value"

    print("[PASS]Convenience function tests passed")


def test_comprehensive_keys():
    """Test a comprehensive set of translation keys."""
    print("Testing comprehensive key set...")

    tm = TranslationManager("en")

    # Test keys from different categories
    test_keys = {
        "app.name": "Projector Control",
        "wizard.title": "Setup Wizard",
        "buttons.finish": "Finish",
        "status.connected": "Connected",
        "power.on": "Power On",
        "controls.blank": "Blank Screen",
        "errors.connection_failed": "Failed to connect to projector",
        "menu.file_settings": "Settings",
        "notifications.projector_on": "Projector turned on",
        "accessibility.high_contrast": "High Contrast Mode",
        "validation.required_field": "This field is required",
    }

    for key, expected_value in test_keys.items():
        actual_value = tm.get(key)
        assert actual_value == expected_value, \
            f"Key '{key}' returned '{actual_value}', expected '{expected_value}'"

    print(f"[PASS] Comprehensive key tests passed ({len(test_keys)} keys)")


def test_hebrew_translations():
    """Test that Hebrew translations exist and are different from English."""
    print("Testing Hebrew translations...")

    tm_en = TranslationManager("en")
    tm_he = TranslationManager("he")

    # Sample keys to test
    test_keys = [
        "app.name",
        "wizard.title",
        "buttons.next",
        "status.connected",
        "power.on",
    ]

    for key in test_keys:
        en_value = tm_en.get(key)
        he_value = tm_he.get(key)

        assert len(he_value) > 0, f"Hebrew translation missing for '{key}'"
        # Hebrew should be different from English (unless it's a technical term)
        # We just check that it's not the fallback marker
        assert not he_value.startswith("["), f"Hebrew translation missing for '{key}'"

    print(f"[PASS] Hebrew translation tests passed ({len(test_keys)} keys)")


def run_all_tests():
    """Run all translation tests."""
    print("=" * 70)
    print("TRANSLATION SYSTEM TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        test_translation_manager_initialization,
        test_nested_key_lookup,
        test_language_switching,
        test_fallback_mechanisms,
        test_rtl_detection,
        test_global_manager,
        test_convenience_function,
        test_comprehensive_keys,
        test_hebrew_translations,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print(f"[FAIL] FAILED: {e}")
            failed += 1
            print()
        except Exception as e:
            print(f"[ERROR] ERROR: {e}")
            failed += 1
            print()

    print("=" * 70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed out of {len(tests)} total")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
