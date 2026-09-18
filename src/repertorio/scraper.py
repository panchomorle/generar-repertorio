import re
import urllib.request
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup, NavigableString, Tag

from repertorio.cleaner import filter_and_clean_lines

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _tokenize_container(container: Any) -> List[List[Dict[str, Any]]]:
    """Tokenize chords and text from a BeautifulSoup container."""
    lines: List[List[Dict[str, Any]]] = []

    divs = container.find_all("div", class_="kvMV")
    nodes_to_process = divs if divs else [container]

    for node in nodes_to_process:
        current_line: List[Dict[str, Any]] = []
        for child in node.children:
            if isinstance(child, Tag) and child.name == "b":
                current_line.append({"text": child.get_text(), "is_chord": True})
            elif isinstance(child, NavigableString):
                parts = str(child).split("\n")
                for i, part in enumerate(parts):
                    if part:
                        current_line.append({"text": part, "is_chord": False})
                    if i < len(parts) - 1:
                        lines.append(current_line)
                        current_line = []
            elif isinstance(child, Tag):
                # Other inline tag, e.g. span or small
                text = child.get_text()
                if text:
                    current_line.append({"text": text, "is_chord": False})

        if current_line:
            lines.append(current_line)

    return lines


def fetch_and_parse_song(dns: str, url: str, artist: str = "", title: str = "", timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Fetch the song page from Cifra Club and extract chords and lyrics."""
    song_url = f"https://www.cifraclub.com.br/{dns}/{url}/"
    req = urllib.request.Request(song_url, headers=DEFAULT_HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")

        # Key (Tom) extraction: support modern CifraClub markup and legacy fallback
        key = None
        btn_tone = soup.find("button", attrs={"data-anchor": "--chord-tone"})
        if btn_tone:
            key = btn_tone.get_text(strip=True)

        if not key:
            for span in soup.find_all(string=re.compile(r"^Tom\b", re.I)):
                parent = span.parent
                if parent:
                    btn = parent.find_next("button") or (parent.parent.find("button") if parent.parent else None)
                    if btn:
                        candidate = btn.get_text(strip=True)
                        if candidate and len(candidate) <= 6:
                            key = candidate
                            break

        if not key:
            key_elem = soup.find(id="cifra_tom") or soup.find("span", id="cifra_tom") or soup.find(attrs={"data-tom": True})
            key = key_elem.get_text(strip=True) if key_elem else None

        capo_elem = soup.find(id="cifra_capo") or soup.find("span", id="cifra_capo")
        capo = capo_elem.get_text(strip=True) if capo_elem else None

        # Pre block containing chords and lyrics
        pre = soup.find("pre", class_="_crVx") or soup.find("pre")
        if not pre:
            print(f"[WARN] No chord pre block found on {song_url}")
            return None

        raw_lines = _tokenize_container(pre)
        clean_lines = filter_and_clean_lines(raw_lines)

        return {
            "artist": artist,
            "title": title,
            "dns": dns,
            "url": url,
            "song_url": song_url,
            "key": key,
            "capo": capo,
            "lines": clean_lines,
        }

    except Exception as exc:
        print(f"[WARN] Failed to fetch or parse {song_url}: {exc}")
        return None
