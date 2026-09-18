# 02: Setlist Song Override and Generator Core

**What to build:** A persistent Song Override model in the Setlist entity and integration into the Repertoire compilation pipeline. When a song is modified, its custom chord sheet is saved as an override bound to that song entry in the setlist without modifying the global CifraClub cache in `.cache_cifras/`. The setlist autosave, export, and import operations preserve the override. When compiling the repertoire document, the generator prioritizes the song override, applies active transposition, and renders the Word document with proper chord coloring and header metadata while keeping original key references intact. A restore operation allows clearing the override to revert to the cached CifraClub source.

**Blocked by:** 01: Harmonic Text Parser and Tokenizer

**Status:** resolved

- [x] A Setlist entry can store an override payload containing custom chord lines and an edit flag.
- [x] Setting an override on a song marks it as modified, and clearing the override reverts the song to its unedited state.
- [x] Song overrides persist across sessions via the setlist autosave file (`setlist.json`) and survive export/import operations.
- [x] Reordering songs (move up/down) or adding new songs to the setlist preserves existing overrides without corruption.
- [x] During repertoire compilation, `generate_from_songs` detects the song override and uses its custom lines instead of loading from the global cache or scraper.
- [x] Transposition applied to a song with an override properly shifts all chords in the override and displays the correct key and original reference in the document header.
- [x] Integration tests verify override persistence and document generation with custom chords.

## Comments

- Added `set_song_override`, `clear_song_override`, `has_song_override`, `is_song_modified`, `get_song_override`, and `get_song_lines` methods to `Setlist` (`src/repertorio/setlist.py`).
- Updated `add_song` to preserve song override payloads across additions, autosave, and export/import cycles.
- Integrated override prioritization into `generate_from_songs` (`src/repertorio/generator.py`), bypassing scraping and keeping `.cache_cifras/` cache immutable while applying active transposition and formatting in Word compilation.
- Added comprehensive unit and integration tests in `tests/test_setlist.py` and `tests/test_generator.py`.

