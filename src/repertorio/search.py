import json
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional, List

SOLR_SEARCH_URL = "https://solr.sscdn.co/cc/c7/?q="
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def search_songs(query: str, limit: int = 10, timeout: int = 10) -> List[Dict[str, Any]]:
    """Search Cifra Club for songs using its internal Solr endpoint.

    Returns a list of dicts with metadata for matching songs:
        [{'artist': str, 'title': str, 'dns': str, 'url': str}, ...]
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    encoded_query = urllib.parse.quote(clean_query)
    full_url = f"{SOLR_SEARCH_URL}{encoded_query}"

    req = urllib.request.Request(full_url, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            docs = data.get("response", {}).get("docs", [])
            results = []
            for doc in docs[:limit]:
                dns = doc.get("dns", "")
                url = doc.get("url", "")
                if dns and url:
                    results.append({
                        "artist": doc.get("art", "Artista Desconocido"),
                        "title": doc.get("txt", clean_query),
                        "dns": dns,
                        "url": url,
                    })
            return results
    except Exception as exc:
        print(f"[WARN] Error searching for '{clean_query}': {exc}")

    return []


def search_song(query: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Search Cifra Club for a single top-matching song. Kept for backward compatibility."""
    results = search_songs(query, limit=1, timeout=timeout)
    return results[0] if results else None
