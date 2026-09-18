# Spec: Song Overrides and Preview Editing in Setlist

Status: ready-for-agent

## Problem Statement

When compiling repertoire songbooks, chord sheets fetched from CifraClub frequently contain elements that disrupt rehearsals or consume unnecessary page space:
1. Long intro tablatures, guitar solos, or Portuguese annotations that crowd the two-column Word layout.
2. Inaccurate chord voicings or lyrics typos that musicians want to correct for their specific arrangements.
3. Verses, bridges, or repeats that the band chooses to skip.

Currently, the application provides no way to view or edit a song's content before compiling. Any manual post-generation corrections in Microsoft Word are immediately overwritten and lost whenever the setlist is updated, reordered, or re-generated.

## Solution

1. **Preview & In-Place Editing Modal**:
   Clicking on any Song in the Setlist launches a modal editor displaying the song's chords and lyrics in a clear monospace layout.
2. **Harmonic Synchronization (WYSIWYG)**:
   The editor renders chords at the song's current transposed pitch, allowing musicians to edit in the actual key they play. Live `[-]` and `[+]` controls update the displayed chords in real time while tracking the cumulative semitone deviation from CifraClub's original key.
3. **Setlist-Level Song Overrides**:
   Edits are saved as a `Song Override` scoped exclusively to that Song entry in the Setlist. The original CifraClub cache in `.cache_cifras/songs/` remains intact, and a "Restaurar original" action lets users roll back to the clean source at any time.
4. **Visual Indicator in Setlist**:
   Songs with custom overrides display a distinct badge (`[✏️ Editada]`) in the Setlist UI for immediate visibility.
5. **Persistent Compilation Pipeline**:
   The Repertoire generator prioritizes the Song Override during compilation, ensuring all custom chord corrections and omitted sections persist across setlist reordering, additions, and re-generations.

## User Stories

1. As a musician, I want to click on a song in my setlist so that I can immediately preview its chords and lyrics before compiling the repertoire.
2. As a performer, I want to edit chords and lyrics directly in the preview window so that I can eliminate unwanted guitar tabs or fix incorrect verses.
3. As a singer, I want the editor to display chords in my currently transposed key so that I don't have to perform mental reverse-transposition when fixing a chord.
4. As a band leader, I want live transposition controls (`+` and `-`) inside the editor modal so that I can adjust the key while reviewing the song's structure.
5. As a musician, I want my edits to be stored as a Setlist-level Song Override so that the original CifraClub version remains safe in cache.
6. As an arranger, I want to see a visual badge (`[✏️ Editada]`) on modified songs in the Setlist so that I know at a glance which tracks have custom changes.
7. As a user, I want a "Restaurar original" button in the editor modal so that I can easily undo all my edits and revert to the original CifraClub chord sheet.
8. As a user, I want my edits to persist automatically across application sessions in `setlist.json` so that I never lose my custom arrangements when closing the app.
9. As a musician, I want the generated Word (.docx) repertoire to render my edited chord sheet with chords bolded and colored in orange, just like unedited songs.
10. As a performer, I want the Word document header to reflect both the transposed key and the original key reference even when the song has custom overrides (e.g. `Tono: A (Original: G)`).
11. As a user, I want to be able to move edited songs up or down in the setlist without losing their custom content.
12. As a user, I want to add more songs to the setlist after editing an existing song without affecting or resetting any previous overrides.
13. As a user, I want any new chords added in the editor (e.g. changing `G` to `Gmaj7`) to be recognized by the harmonic parser and transposed accurately if I later adjust the key.
14. As a user, I want the modal editor to close cleanly when clicking "Cancelar" or pressing Escape without saving unintended alterations.
15. As a user, I want exporting and importing setlists to preserve song overrides so that custom arrangements can be shared or backed up.

## Implementation Decisions

- **Domain Model Extension**:
  - The `Setlist` entity stores an optional `override` payload per song dict, containing `lines` (the tokenized structure of lines and chords) and an `is_modified` flag.
  - The underlying global cache in `.cache_cifras/songs/` remains completely unmodified.
  - Methods added to `Setlist`: `set_song_override(index, override_lines)`, `clear_song_override(index)`, and `get_song_lines(index)`.
- **Harmonic Text Parser & Re-tokenizer**:
  - A parsing function converts user-edited plain text (monospace lines of chords above lyrics) back into structured tokens (`[{"text": "...", "is_chord": bool}]`).
  - Lines containing standard chord notation tokens (matching `CHORD_PATTERN`) are recognized and tagged as chords, preserving character offsets and indentation.
- **Harmonic Transposition Preservation**:
  - When editing a song with `semitones != 0`, chords are shown transposed.
  - Upon saving, chords are stored normalized relative to the song's base key using the inverse offset `-semitones`, ensuring subsequent transposition delta adjustments in the Setlist remain mathematically exact.
- **UI Modal (CustomTkinter Toplevel)**:
  - Clicking on a song row in the Setlist table launches a modal `CTkToplevel` window.
  - The modal features a header with song title, artist, active key, and `[-]`/`[+]` transposition buttons.
  - A large `CTkTextbox` with monospace font (`Consolas`) holds the chord sheet text.
  - A footer provides "Guardar cambios", "Restaurar original" (enabled only if the song has an override), and "Cerrar" buttons.
- **Generator Integration**:
  - `generate_from_songs` in the generation pipeline checks if the song has an `override` before querying cache or scraper. If present, it uses the override lines, applies `transpose_lines` with the song's active `semitones`, and builds the document section.

## Testing Decisions

- **Good Test Criteria**: Tests must verify observable external behavior (adding overrides, persisting setlists, compiling repertoires, transposing edited chords) without asserting on internal GUI widget placements or private helper mechanics.
- **Target Modules**:
  - `Setlist` state and persistence: Verifying overrides survive autosave, reloads, and export/import.
  - Chord parser & re-tokenizer: Verifying that plain text chord sheets are accurately tokenized and chords are distinguished from lyrics.
  - `generator` pipeline: Verifying that `generate_from_songs` accurately compiles Word documents using override chord sheets with proper transposition and colors.
- **Prior Art**:
  - `tests/test_setlist.py`: Prior art for testing setlist operations and JSON autosave persistence.
  - `tests/test_transposer.py`: Prior art for testing chord shifting and line transposition.
  - `tests/test_generator.py`: Prior art for testing document compilation with mocked songs.

## Out of Scope

- Rich-text inline chord styling or WYSIWYG word-processor formatting inside the desktop app (plain monospace chord sheet text is used).
- Global overrides across different setlists or mutating CifraClub's upstream content.
- Automatic lyric spell-checking or grammar correction.

## Further Notes

- Documented in ADR-0004 (`docs/adr/0004-song-overrides-and-preview-editing.md`).
- Domain glossary in `CONTEXT.md` updated with `Song Override`.
