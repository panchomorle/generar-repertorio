import json
from pathlib import Path
import pytest

import repertorio
from repertorio.settings import (
    DEFAULT_SETTINGS_PATH,
    DEFAULT_COLUMNS,
    DEFAULT_CHORD_COLOR,
    SettingsManager,
    validate_columns,
    validate_chord_color,
)


def test_default_constants():
    assert DEFAULT_SETTINGS_PATH == Path(".cache_cifras") / "settings.json"
    assert DEFAULT_COLUMNS == 2
    assert DEFAULT_CHORD_COLOR == "#E65100"


def test_package_exports():
    assert repertorio.SettingsManager is SettingsManager
    assert repertorio.DEFAULT_SETTINGS_PATH == DEFAULT_SETTINGS_PATH
    assert repertorio.DEFAULT_COLUMNS == DEFAULT_COLUMNS
    assert repertorio.DEFAULT_CHORD_COLOR == DEFAULT_CHORD_COLOR


def test_default_values_when_file_does_not_exist(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    assert not settings_file.exists()

    manager = SettingsManager(persistence_path=settings_file)

    assert manager.columns == 2
    assert manager.chord_color == "#E65100"
    assert manager.persistence_path == settings_file
    assert manager.to_dict() == {"columns": 2, "chord_color": "#E65100"}


def test_save_valid_settings_and_reload(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    manager = SettingsManager(persistence_path=settings_file)

    # Save 1 column and custom black chord color
    manager.save(columns=1, chord_color="#000000")
    assert manager.columns == 1
    assert manager.chord_color == "#000000"
    assert settings_file.exists()

    # Verify JSON format on disk
    with open(settings_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {"columns": 1, "chord_color": "#000000"}

    # Reload in a new instance
    reloaded = SettingsManager(persistence_path=settings_file)
    assert reloaded.columns == 1
    assert reloaded.chord_color == "#000000"

    # Test uppercase normalization and 2 columns
    reloaded.update(columns=2, chord_color="#ffffff")
    assert reloaded.columns == 2
    assert reloaded.chord_color == "#FFFFFF"

    # Reload again
    reloaded_again = SettingsManager(persistence_path=settings_file)
    assert reloaded_again.columns == 2
    assert reloaded_again.chord_color == "#FFFFFF"

    # Test another custom color
    reloaded_again.update(columns=1, chord_color="#123456")
    assert reloaded_again.columns == 1
    assert reloaded_again.chord_color == "#123456"


def test_graceful_recovery_corrupted_json(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{invalid json", encoding="utf-8")

    manager = SettingsManager(persistence_path=settings_file)

    assert manager.columns == DEFAULT_COLUMNS
    assert manager.chord_color == DEFAULT_CHORD_COLOR
    assert manager.to_dict() == {"columns": 2, "chord_color": "#E65100"}


def test_graceful_recovery_empty_file(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("", encoding="utf-8")

    manager = SettingsManager(persistence_path=settings_file)

    assert manager.columns == DEFAULT_COLUMNS
    assert manager.chord_color == DEFAULT_CHORD_COLOR
    assert manager.to_dict() == {"columns": 2, "chord_color": "#E65100"}


def test_graceful_recovery_partial_missing_keys(tmp_path: Path):
    settings_file = tmp_path / "settings.json"

    # Missing chord_color
    settings_file.write_text(json.dumps({"columns": 1}), encoding="utf-8")
    manager = SettingsManager(persistence_path=settings_file)
    assert manager.columns == 1
    assert manager.chord_color == DEFAULT_CHORD_COLOR

    # Missing columns
    settings_file.write_text(json.dumps({"chord_color": "#000000"}), encoding="utf-8")
    manager2 = SettingsManager(persistence_path=settings_file)
    assert manager2.columns == DEFAULT_COLUMNS
    assert manager2.chord_color == "#000000"


def test_fallback_on_invalid_types(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps({"columns": "invalid", "chord_color": 123}), encoding="utf-8"
    )

    manager = SettingsManager(persistence_path=settings_file)
    assert manager.columns == DEFAULT_COLUMNS
    assert manager.chord_color == DEFAULT_CHORD_COLOR


def test_fallback_on_out_of_range_columns(tmp_path: Path):
    settings_file = tmp_path / "settings.json"

    for invalid_col in [3, 0, -1, 100]:
        settings_file.write_text(
            json.dumps({"columns": invalid_col, "chord_color": "#E65100"}),
            encoding="utf-8",
        )
        manager = SettingsManager(persistence_path=settings_file)
        assert manager.columns == DEFAULT_COLUMNS

    # Programmatic update with invalid columns should fall back to default
    manager = SettingsManager(persistence_path=settings_file)
    manager.update(columns=3)
    assert manager.columns == DEFAULT_COLUMNS

    manager.update(columns=True)  # boolean should not pass as int
    assert manager.columns == DEFAULT_COLUMNS


def test_fallback_on_invalid_color_formats(tmp_path: Path):
    settings_file = tmp_path / "settings.json"

    invalid_colors = ["not-a-color", "#GGGGGG", "#FFF", "FFFFFF", "#1234567", "", None]
    for invalid_color in invalid_colors:
        settings_file.write_text(
            json.dumps({"columns": 2, "chord_color": invalid_color}),
            encoding="utf-8",
        )
        manager = SettingsManager(persistence_path=settings_file)
        assert manager.chord_color == DEFAULT_CHORD_COLOR

    # Programmatic update with invalid color
    manager = SettingsManager(persistence_path=settings_file)
    manager.update(chord_color="invalid")
    assert manager.chord_color == DEFAULT_CHORD_COLOR


def test_directory_creation_when_parent_does_not_exist(tmp_path: Path):
    nested_file = tmp_path / "nested" / "dir" / "settings.json"
    assert not nested_file.parent.exists()

    manager = SettingsManager(persistence_path=nested_file)
    manager.save(columns=1, chord_color="#000000")

    assert nested_file.exists()
    assert nested_file.parent.exists()

    reloaded = SettingsManager(persistence_path=nested_file)
    assert reloaded.columns == 1
    assert reloaded.chord_color == "#000000"


def test_reset_to_defaults(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    manager = SettingsManager(persistence_path=settings_file)

    manager.update(columns=1, chord_color="#000000")
    assert manager.columns == 1
    assert manager.chord_color == "#000000"

    manager.reset_to_defaults()
    assert manager.columns == DEFAULT_COLUMNS
    assert manager.chord_color == DEFAULT_CHORD_COLOR

    reloaded = SettingsManager(persistence_path=settings_file)
    assert reloaded.columns == DEFAULT_COLUMNS
    assert reloaded.chord_color == DEFAULT_CHORD_COLOR


def test_non_dict_json_recovery(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    manager = SettingsManager(persistence_path=settings_file)
    assert manager.columns == DEFAULT_COLUMNS
    assert manager.chord_color == DEFAULT_CHORD_COLOR


def test_validation_helpers():
    assert validate_columns(1) == 1
    assert validate_columns(2) == 2
    assert validate_columns(0) == DEFAULT_COLUMNS
    assert validate_columns(3) == DEFAULT_COLUMNS
    assert validate_columns(-1) == DEFAULT_COLUMNS
    assert validate_columns("1") == DEFAULT_COLUMNS
    assert validate_columns(True) == DEFAULT_COLUMNS
    assert validate_columns(False) == DEFAULT_COLUMNS
    assert validate_columns(None) == DEFAULT_COLUMNS

    assert validate_chord_color("#e65100") == "#E65100"
    assert validate_chord_color("#000000") == "#000000"
    assert validate_chord_color("#FFFFFF") == "#FFFFFF"
    assert validate_chord_color(" #123456 ") == "#123456"
    assert validate_chord_color("#123") == DEFAULT_CHORD_COLOR
    assert validate_chord_color("123456") == DEFAULT_CHORD_COLOR
    assert validate_chord_color("not-color") == DEFAULT_CHORD_COLOR
    assert validate_chord_color(123) == DEFAULT_CHORD_COLOR
    assert validate_chord_color(None) == DEFAULT_CHORD_COLOR
