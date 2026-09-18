# 02: Setlist Song Override and Generator Core

**What to build:** A persistent Song Override model in the Setlist entity and integration into the Repertoire compilation pipeline. When a song is modified, its custom chord sheet is saved as an override bound to that song entry in the setlist without modifying the global CifraClub cache in `.cache_cifras/`. The setlist autosave, export, and import operations preserve the override. When compiling the repertoire document, the generator prioritizes the song override, applies active transposition, and renders the Word document with proper chord coloring and header metadata while keeping original key references intact. A restore operation allows clearing the override to revert to the cached CifraClub source.

**Blocked by:** 01: Harmonic Text Parser and Tokenizer

**Status:** ready-for-agent

- [ ] A Setlist entry can store an override payload containing custom chord lines and an edit flag.
- [ ] Setting an override on a song marks it as modified, and clearing the override reverts the song to its unedited state.
- [ ] Song overrides persist across sessions via the setlist autosave file (`setlist.json`) and survive export/import operations.
- [ ] Reordering songs (move up/down) or adding new songs to the setlist preserves existing overrides without corruption.
- [ ] During repertoire compilation, `generate_from_songs` detects the song override and uses its custom lines instead of loading from the global cache or scraper.
- [ ] Transposition applied to a song with an override properly shifts all chords in the override and displays the correct key and original reference in the document header.
- [ ] Integration tests verify override persistence and document generation with custom chords.
