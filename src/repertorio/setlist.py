import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_SETLIST_PATH = Path(".cache_cifras") / "setlist.json"


class Setlist:
    """Manages the ordered, curated list of songs for a repertoire."""

    def __init__(self, persistence_path: Path | str = DEFAULT_SETLIST_PATH) -> None:
        self.persistence_path = Path(persistence_path)
        self.songs: List[Dict[str, Any]] = []
        self.load_autosave()

    def add_song(self, song: Dict[str, Any]) -> bool:
        """Add a song dict with artist, title, dns, url. Returns True if added."""
        required = {"artist", "title", "dns", "url"}
        if not required.issubset(song.keys()):
            return False

        # Avoid exact duplicate slug in setlist
        slug = f"{song['dns']}_{song['url']}"
        for existing in self.songs:
            if f"{existing.get('dns')}_{existing.get('url')}" == slug:
                return False

        song_entry = {
            "artist": song["artist"],
            "title": song["title"],
            "dns": song["dns"],
            "url": song["url"],
            "key": song.get("key"),
            "semitones": int(song.get("semitones", 0)),
        }
        if "override" in song and song["override"] is not None:
            song_entry["override"] = song["override"]

        self.songs.append(song_entry)
        self.save_autosave()
        return True

    def set_song_override(
        self, index: int, override_lines: List[List[Dict[str, Any]]] | str
    ) -> bool:
        """Set a custom chord sheet override for a song at index. Returns True if set."""
        if 0 <= index < len(self.songs):
            if isinstance(override_lines, str):
                from repertorio.parser import parse_text_to_lines
                lines = parse_text_to_lines(override_lines)
            else:
                lines = override_lines

            self.songs[index]["override"] = {
                "lines": lines,
                "is_modified": True,
            }
            self.save_autosave()
            return True
        return False

    def clear_song_override(self, index: int) -> bool:
        """Clear song override at index, reverting to unedited state. Returns True if cleared."""
        if 0 <= index < len(self.songs):
            if "override" in self.songs[index]:
                self.songs[index].pop("override", None)
                self.save_autosave()
                return True
        return False

    def has_song_override(self, index: int) -> bool:
        """Return True if song at index has an active override."""
        if 0 <= index < len(self.songs):
            override = self.songs[index].get("override")
            if isinstance(override, dict):
                return bool(override.get("is_modified") and override.get("lines") is not None)
        return False

    def is_song_modified(self, index: int) -> bool:
        """Check if the song at index has been modified with an override."""
        return self.has_song_override(index)

    def get_song_override(self, index: int) -> Optional[Dict[str, Any]]:
        """Return the override payload for a song at index, or None."""
        if 0 <= index < len(self.songs):
            return self.songs[index].get("override")
        return None

    def get_song_lines(
        self,
        index: int,
        cache: Optional[Any] = None,
        cache_dir: Path | str = ".cache_cifras",
    ) -> Optional[List[List[Dict[str, Any]]]]:
        """Return the lines for a song at index, prioritizing override over cache."""
        if not (0 <= index < len(self.songs)):
            return None

        song = self.songs[index]
        override = song.get("override")
        if isinstance(override, dict) and override.get("lines") is not None:
            return override["lines"]

        dns = song.get("dns", "")
        url = song.get("url", "")
        slug = f"{dns}_{url}"
        if slug != "_":
            if cache is None:
                from repertorio.cache import CacheManager
                cache = CacheManager(cache_dir)
            cached_song = cache.get_by_slug(slug)
            if cached_song and "lines" in cached_song:
                return cached_song["lines"]

        return None

    def set_song_key(self, index: int, key: Optional[str]) -> bool:
        """Set the key for a song at index. Returns True if updated."""
        if 0 <= index < len(self.songs):
            self.songs[index]["key"] = key
            self.save_autosave()
            return True
        return False

    def transpose_song(self, index: int, semitones_delta: int) -> Optional[int]:
        """Adjust song transposition by semitones_delta. Returns new semitones value or None."""
        if 0 <= index < len(self.songs):
            current = int(self.songs[index].get("semitones", 0))
            new_val = current + semitones_delta
            self.songs[index]["semitones"] = new_val
            self.save_autosave()
            return new_val
        return None

    def remove_song(self, index: int) -> Optional[Dict[str, Any]]:
        """Remove song at index. Returns removed song or None."""
        if 0 <= index < len(self.songs):
            removed = self.songs.pop(index)
            self.save_autosave()
            return removed
        return None

    def move_up(self, index: int) -> bool:
        """Move song at index one position up. Returns True if moved."""
        if 1 <= index < len(self.songs):
            self.songs[index - 1], self.songs[index] = self.songs[index], self.songs[index - 1]
            self.save_autosave()
            return True
        return False

    def move_down(self, index: int) -> bool:
        """Move song at index one position down. Returns True if moved."""
        if 0 <= index < len(self.songs) - 1:
            self.songs[index + 1], self.songs[index] = self.songs[index], self.songs[index + 1]
            self.save_autosave()
            return True
        return False

    def clear(self) -> None:
        """Clear all songs from setlist."""
        self.songs.clear()
        self.save_autosave()

    def save_autosave(self) -> None:
        """Autosave current setlist to local cache."""
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(self.songs, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[WARN] Error autosaving setlist: {exc}")

    def load_autosave(self) -> None:
        """Load setlist from local cache if exists."""
        if self.persistence_path.exists():
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.songs = data
            except Exception as exc:
                print(f"[WARN] Error loading setlist cache: {exc}")

    def export_to_file(self, file_path: Path | str) -> None:
        """Export setlist to a specific JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.songs, f, ensure_ascii=False, indent=2)

    def import_from_file(self, file_path: Path | str) -> int:
        """Import songs from a JSON file, appending new ones. Returns count added."""
        path = Path(file_path)
        if not path.exists():
            return 0
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        added_count = 0
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and self.add_song(item):
                    added_count += 1
        return added_count
