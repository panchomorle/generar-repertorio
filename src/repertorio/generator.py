from pathlib import Path
from typing import Dict, List, Any

from repertorio.search import search_song
from repertorio.scraper import fetch_and_parse_song
from repertorio.cache import CacheManager
from repertorio.docx_builder import build_document


def read_song_queries(songs_file: Path | str) -> List[str]:
    """Read song queries from a text file, ignoring empty lines and comments."""
    path = Path(songs_file)
    if not path.exists():
        return []

    queries = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("#"):
                queries.append(cleaned)
    return queries


def generate_repertoire(
    songs_file: Path | str,
    output_docx: Path | str,
    cache_dir: Path | str = ".cache_cifras",
) -> Dict[str, int]:
    """Orchestrate reading queries, resolving, caching, and generating the repertoire docx."""
    queries = read_song_queries(songs_file)
    cache = CacheManager(cache_dir)

    resolved_songs: List[Dict[str, Any]] = []
    downloaded = 0
    cached = 0
    failed = 0

    print(f"[*] Procesando {len(queries)} canciones desde {songs_file}...")

    for query in queries:
        # 1. Check cache by query index
        song_data = cache.get_by_query(query)
        if song_data:
            print(f"  [CACHE] {song_data.get('title')} - {song_data.get('artist')} ({query})")
            resolved_songs.append(song_data)
            cached += 1
            continue

        # 2. Search Cifra Club
        match = search_song(query)
        if not match:
            print(f"  [ERROR] No se encontraron resultados para: '{query}'")
            failed += 1
            continue

        dns = match["dns"]
        url = match["url"]
        artist = match["artist"]
        title = match["title"]
        slug_key = f"{dns}_{url}"

        # 3. Check cache by canonical slug
        song_data = cache.get_by_slug(slug_key)
        if song_data:
            print(f"  [CACHE] {title} - {artist} ({query})")
            cache.save(slug_key, song_data, query=query)
            resolved_songs.append(song_data)
            cached += 1
            continue

        # 4. Fetch and parse song page
        print(f"  [BAJANDO] {title} - {artist} desde Cifra Club...")
        song_data = fetch_and_parse_song(dns, url, artist=artist, title=title)
        if not song_data:
            print(f"  [ERROR] Fallo al descargar o parsear: '{query}'")
            failed += 1
            continue

        # Save to cache with query mapping
        cache.save(slug_key, song_data, query=query)

        resolved_songs.append(song_data)
        downloaded += 1

    # 5. Build Word document
    if resolved_songs:
        print(f"[*] Generando documento Word en: {output_docx}...")
        build_document(resolved_songs, output_docx)
        print(f"[+] Documento generado exitosamente con {len(resolved_songs)} canciones.")
    else:
        print("[WARN] No se resolvio ninguna cancion. No se genero el archivo Word.")

    return {
        "total": len(queries),
        "downloaded": downloaded,
        "cached": cached,
        "failed": failed,
    }
