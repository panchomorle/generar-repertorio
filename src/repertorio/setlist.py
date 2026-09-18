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

        self.songs.append({
            "artist": song["artist"],
            "title": song["title"],
            "dns": song["dns"],
            "url": song["url"],
        })
        self.save_autosave()
        return True

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
