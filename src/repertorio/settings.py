import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_SETTINGS_PATH = Path(".cache_cifras") / "settings.json"
DEFAULT_COLUMNS: int = 2
DEFAULT_CHORD_COLOR: str = "#E65100"

HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def validate_columns(val: Any) -> int:
    """Validate column layout choice. Must be integer 1 or 2; falls back to DEFAULT_COLUMNS."""
    if isinstance(val, int) and not isinstance(val, bool) and val in (1, 2):
        return val
    return DEFAULT_COLUMNS


def validate_chord_color(val: Any) -> str:
    """Validate hex chord color string. Must be 6-hex digits prefixed with '#'; falls back to DEFAULT_CHORD_COLOR."""
    if isinstance(val, str) and HEX_COLOR_PATTERN.match(val.strip()):
        return val.strip().upper()
    return DEFAULT_CHORD_COLOR


class SettingsManager:
    """Manages local user settings persistence for repertoire generation preferences."""

    def __init__(self, persistence_path: Path | str = DEFAULT_SETTINGS_PATH) -> None:
        self.persistence_path = Path(persistence_path)
        self._columns: int = DEFAULT_COLUMNS
        self._chord_color: str = DEFAULT_CHORD_COLOR
        self.load()

    @property
    def columns(self) -> int:
        return self._columns

    @columns.setter
    def columns(self, value: Any) -> None:
        self._columns = validate_columns(value)

    @property
    def chord_color(self) -> str:
        return self._chord_color

    @chord_color.setter
    def chord_color(self, value: Any) -> None:
        self._chord_color = validate_chord_color(value)

    def load(self) -> Dict[str, Any]:
        """Loads settings from disk. Safely falls back to defaults on missing, empty, or corrupt files."""
        if not self.persistence_path.exists():
            self._columns = DEFAULT_COLUMNS
            self._chord_color = DEFAULT_CHORD_COLOR
            return self.to_dict()

        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                if "columns" in data:
                    self.columns = data["columns"]
                else:
                    self.columns = DEFAULT_COLUMNS

                if "chord_color" in data:
                    self.chord_color = data["chord_color"]
                else:
                    self.chord_color = DEFAULT_CHORD_COLOR
            else:
                self.columns = DEFAULT_COLUMNS
                self.chord_color = DEFAULT_CHORD_COLOR
        except Exception:
            self.columns = DEFAULT_COLUMNS
            self.chord_color = DEFAULT_CHORD_COLOR

        return self.to_dict()

    def save(
        self,
        columns: Optional[int] = None,
        chord_color: Optional[str] = None,
    ) -> None:
        """Persists settings to disk as formatted JSON, creating parent directories if needed."""
        if columns is not None:
            self.columns = columns
        if chord_color is not None:
            self.chord_color = chord_color

        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def update(
        self,
        columns: Optional[int] = None,
        chord_color: Optional[str] = None,
    ) -> None:
        """Updates in-memory values (with validation) and saves to disk."""
        self.save(columns=columns, chord_color=chord_color)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the current settings as a dictionary."""
        return {
            "columns": self.columns,
            "chord_color": self.chord_color,
        }

    def reset_to_defaults(self) -> None:
        """Resets settings to default values and saves to disk."""
        self.columns = DEFAULT_COLUMNS
        self.chord_color = DEFAULT_CHORD_COLOR
        self.save()
