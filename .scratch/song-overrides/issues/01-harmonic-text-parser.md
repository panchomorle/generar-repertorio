# 01: Harmonic Text Parser and Tokenizer

**What to build:** A bidirectional parsing module that converts user-edited monospace chord sheets (where chord lines are placed above lyric lines, as in CifraClub) into tokenized lines of chords and text, and formats tokenized lines back into clean monospace text for display in the editor. The parser distinguishes chord lines from lyrics, preserves chord column offsets and spacing, and ensures edited or newly added chords are tagged as transposable chords.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Given a plain text chord sheet string with chords above lyrics, parsing it produces structured line tokens where chords have their chord flag set to true and character column offsets preserved.
- [x] Given structured line tokens, formatting it produces clean monospace text suitable for editing in a text area.
- [x] Lines containing standard chord notation tokens (simple chords, slash chords like `D/F#`, tensions, altered chords) are recognized and distinguished from regular lyrics lines.
- [x] Empty lines, indentation, and structural section labels (e.g. `[Intro]`, `[Estribillo]`) are handled cleanly without misclassifying lyric text as chords.
- [x] Unit tests verify parsing, formatting, and roundtrip consistency across various chord sheet formats.

## Comments

Implemented bidirectional parsing in `src/repertorio/parser.py` (`parse_text_to_lines`, `format_lines_to_text`, `is_chord_token`, `is_chord_line`) and verified with comprehensive unit tests in `tests/test_parser.py`.

