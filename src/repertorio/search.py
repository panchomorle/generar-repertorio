import json
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional

SOLR_SEARCH_URL = "https://solr.sscdn.co/cc/c7/?q="
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def search_song(query: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Search Cifra Club for a song using its internal Solr endpoint.

    Returns a dict with metadata for the most popular match:
        {'art': str, 'txt': str, 'dns': str, 'url': str}
    or None if no match is found.
    """
    clean_query = query.strip()
    if not clean_query:
        return None

    encoded_query = urllib.parse.quote(clean_query)
    full_url = f"{SOLR_SEARCH_URL}{encoded_query}"

    req = urllib.request.Request(full_url, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            docs = data.get("response", {}).get("docs", [])
            if docs:
                top_match = docs[0]
                return {
                    "artist": top_match.get("art", "Artista Desconocido"),
                    "title": top_match.get("txt", clean_query),
                    "dns": top_match.get("dns", ""),
                    "url": top_match.get("url", ""),
                }
    except Exception as exc:
        print(f"[WARN] Error searching for '{clean_query}': {exc}")

    return None
