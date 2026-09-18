# 01: Layout Presets and Chord Color in Repertoire Engine

**What to build:** Configurable column layout support (1 or 2 columns) with automatic typography presets and custom chord color rendering in the Repertoire document generation engine. When generating a document with 1 column (screen/tablet mode), the engine formats the Word section as a single column and automatically applies an enlarged monospace font (10.5 pt) with matched line spacing (13 pt) for distance reading. When generating with 2 columns (print mode), it formats two columns with compact font (8.5 pt) and spacing (10.5 pt). Additionally, chords are rendered using a configurable color (defaulting to brand orange `#E65100`), allowing solid black for crisp contrast on monochrome printers.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [x] Generating a Repertoire with 1 column produces a Word document with a single-column section (`w:cols num="1"`).
- [x] In 1-column documents, chord and lyrics text automatically adopts the 10.5 pt font size preset with 13 pt line spacing.
- [x] Generating a Repertoire with 2 columns produces a Word document with a two-column section (`w:cols num="2"`).
- [x] In 2-column documents, chord and lyrics text automatically adopts the 8.5 pt font size preset with 10.5 pt line spacing.
- [x] Chords are rendered in the configured color (e.g. solid black `#000000` or custom RGB), defaulting to orange `#E65100` when omitted.
- [x] Repertoire generation with transposed songs or custom song overrides correctly inherits the chosen column layout, typography presets, and chord color.
- [x] Automated integration tests verify generated Word documents for column properties, run font sizes, and run RGB colors across both layout presets.
