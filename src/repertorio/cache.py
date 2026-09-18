import json
import re
from pathlib import Path
from typing import Dict, Any, Optional


def sanitize_filename(key: str) -> str:
    """Sanitize a key string to be used safely as a filename."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", key.strip().lower())


class CacheManager:
    """Manages local JSON file cache for song details and query index."""

    def __init__(self, cache_dir: Path | str = ".cache_cifras"):
        self.cache_dir = Path(cache_dir)
        self.songs_dir = self.cache_dir / "songs"
        self.index_file = self.cache_dir / "index.json"

        self.songs_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, str] = self._load_index()

    def _load_index(self) -> Dict[str, str]:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                print(f"[WARN] Error reading cache index {self.index_file}: {exc}")
        return {}

    def _save_index(self) -> None:
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[WARN] Error saving cache index {self.index_file}: {exc}")

    def get_by_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Find cached song data mapped to a search query."""
        slug = self._index.get(query.strip().lower())
        if slug:
            return self.get_by_slug(slug)
        return None

    def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached song data by canonical slug."""
        filename = f"{sanitize_filename(slug)}.json"
        path = self.songs_dir / filename
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                print(f"[WARN] Error reading song cache {path}: {exc}")
        return None

    def save(self, slug: str, data: Dict[str, Any], query: Optional[str] = None) -> None:
        """Save canonical song data and optionally index the query pointing to it."""
        filename = f"{sanitize_filename(slug)}.json"
        path = self.songs_dir / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[WARN] Error saving song cache {path}: {exc}")

        if query:
            self._index[query.strip().lower()] = slug
            self._save_index()
