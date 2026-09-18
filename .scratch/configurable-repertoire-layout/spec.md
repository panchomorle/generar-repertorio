# Spec: Configurable Repertoire Layout and Chord Color

Status: done

## Problem Statement

Musicians use the compiled Word Repertoire in two very distinct environments: reading live from a digital screen (tablet or phone on a music stand) versus printing physical copies on paper for band rehearsals.

Currently:
1. The Repertoire generator hardcodes a 2-column layout and a fixed font size of 8.5 pt.
2. When viewed on a tablet or screen, a 2-column layout forces awkward reading angles, and 8.5 pt monospace text leaves large portions of the screen underutilized while being difficult to read from standing or performance distance.
3. Conversely, physical printing benefits greatly from 2 columns to save paper, but the hardcoded bright orange chord color (`#E65100`) often renders as a faint, dithered gray on standard monochrome laser printers, diminishing contrast and readability under stage lighting.
4. Users have no controls in the application interface to choose between a single-column screen-optimized layout and a two-column print-optimized layout, nor can they customize chord colors or preserve their formatting preferences across sessions.

## Solution

1. **Configurable Column Layout**:
   Allow selecting between 1 column and 2 columns for the compiled Repertoire document.
2. **Automatic Typography Presets**:
   Couple font size and line spacing presets directly to the chosen column layout:
   - **1 Column (Screen/Tablet mode)**: 10.5 pt font with 13 pt line spacing, maximizing readability at performance distance without text wrapping.
   - **2 Columns (Print mode)**: 8.5 pt font with 10.5 pt line spacing, maintaining compact structure so multi-bar chord sequences fit neatly within column margins.
3. **UI Layout Controls & Adaptive Hint**:
   Add a dedicated format row in the generation panel featuring:
   - A segmented selector for 1 Column vs. 2 Columns.
   - A subtle explanatory hint: *"1 columna se adapta mejor a pantallas · 2 columnas es mejor para imprimir"*.
4. **Decoupled Chord Color Picker**:
   Provide a discrete, compact button displaying a swatch of the current chord color. Clicking it opens the native operating system color picker dialog, allowing musicians to pick custom colors (e.g. solid black for high-contrast monochrome printing, or custom stage colors), defaulting to brand orange (`#E65100`).
5. **Persistent Local Preferences**:
   Persist the user's selected column count and chord color locally in `.cache_cifras/settings.json`, ensuring their preferred rehearsal or gig layout is instantly restored whenever the application launches.
6. **Glossary & Domain Realignment**:
   Update `CONTEXT.md` to broaden the definition of Repertoire from a fixed two-column document to a configurable single or multi-column layout.

## User Stories

1. As a gigging musician performing with a tablet on my music stand, I want to generate a 1-column Repertoire so that lyrics and chords fill the screen in a comfortable reading flow.
2. As a musician reading at performance distance, I want 1-column documents to automatically use a larger font size (10.5 pt) so that I can read chords clearly without squinting or leaning in.
3. As a band leader preparing rehearsal handouts, I want to generate a 2-column Repertoire so that songs fit onto fewer printed pages and save paper.
4. As a user configuring the output document, I want to see an informative hint explaining that 1 column is best for screens and 2 columns is best for printing so that I make the right choice without trial and error.
5. As a musician printing on a black-and-white laser printer, I want to customize the chord color to solid black so that chords print with crisp contrast instead of washed-out grayscale halftone.
6. As a guitarist who likes the signature orange chord aesthetic, I want orange (`#E65100`) to be the default chord color so that existing behavior is preserved out of the box.
7. As an application user, I want the chord color control to be a compact, discrete button with a color preview swatch so that it does not clutter or distract from the main interface.
8. As a user selecting a chord color, I want the operating system's native color chooser to open when clicking the swatch so that I have complete freedom to select or fine-tune any color.
9. As a musician who exclusively uses a tablet, I want the application to remember my 1-column preference across restarts so that I do not have to reconfigure it every time I open the app.
10. As a musician with a custom chord color preference, I want my selected color to persist locally on my machine across sessions so that my exported documents are always consistent.
11. As a user importing or sharing a Setlist, I want Setlist files to remain focused purely on the songs and their musical keys, while format preferences stay as application-level generation settings.
12. As an existing user running the CLI or generator pipeline programmatically, I want the generator functions to accept optional layout and color arguments while gracefully falling back to standard defaults (2 columns, orange color).
13. As a performer with edited songs (Song Overrides), I want the selected column layout, typography preset, and chord color to apply seamlessly to both original and edited songs.
14. As a performer using transposition, I want transposed chord sheets to respect the chosen column layout and chord color without affecting musical transposition calculations.
15. As a user generating a Repertoire, I want immediate visual confirmation of the chosen layout in the generated Word document with correct Word section column properties.

## Implementation Decisions

- **Domain Model Evolution**:
  - The definition of `Repertoire` in the project glossary is generalized to denote compiled Word documents with single or multi-column layouts and adaptive typography.
  - Formatting settings are modeled as application/generation concerns rather than embedded into the `Setlist` domain entity, keeping setlist data portable across different export targets.
- **Document Rendering Pipeline**:
  - The document builder accepts layout parameters: column count (integer: 1 or 2) and chord color (RGB values or hex string).
  - An internal preset map defines typography metrics per column count:
    - 1 column: Font size 10.5 pt, line spacing 13 pt.
    - 2 columns: Font size 8.5 pt, line spacing 10.5 pt.
  - Section columns in the underlying OpenXML format are configured accordingly (`w:cols num="1"` or `num="2"`).
  - Paragraph runs with chord tokens apply the dynamically provided chord color instead of a static constant.
- **Local Settings Persistence**:
  - A settings manager handles reading and writing application preferences to a local JSON file (`.cache_cifras/settings.json`).
  - Default preferences: `{ "columns": 2, "chord_color": "#E65100" }`.
  - Fallback mechanisms ensure that corrupted or missing settings files transparently return valid defaults without crashing the app.
- **Desktop UI Integration**:
  - A compact options row is positioned inside the generation frame in the main window.
  - Layout toggle uses a segmented button control (`1 Columna` | `2 Columnas`).
  - An informational label is rendered adjacent to the toggle with dimmed styling displaying the adaptive hint.
  - A square preview button shows the currently active chord color; clicking it invokes the native color picker dialog and immediately updates the preview swatch and local settings.
  - The generation worker passes the active settings into the generator pipeline.
- **Architectural Documentation**:
  - ADR-0005 is recorded in the project's architectural decisions directory, detailing the rationale behind automatic typography coupling, decoupling chord colors, and using application-level local persistence.

## Testing Decisions

- **Good Test Criteria**: Tests must verify observable document output (correct Word XML column attributes, paragraph run font sizes, and run RGB colors) and settings file persistence, without asserting on internal GUI widget placements or transient GUI event loop state.
- **Testing Seams**:
  - **Highest Seam (Generator Pipeline)**: `generate_from_songs` is the primary integration seam. Tests will invoke generation with varied column counts (1 vs. 2) and custom chord colors, verifying the generated `.docx` document's section column XML, run font sizes, and run font colors.
  - **Settings Persistence Seam**: Unit tests verifying that the settings manager correctly loads existing JSON, saves updates, and provides safe defaults when files are missing or malformed.
- **Prior Art**:
  - `tests/test_generator.py`: Existing tests that inspect generated docx OpenXML sections (`xpath("./w:cols")`) and run font properties (`r.font.color.rgb`, `r.font.size`).
  - `tests/test_setlist.py`: Existing pattern for testing local JSON persistence with isolated temporary directories.

## Out of Scope

- Arbitrary column counts (3+ columns) or custom column width ratios.
- Manual font size sliders or custom font family selectors.
- Page margin customizations or paper size selection (A4 vs. Letter).
- Per-song formatting overrides (all songs in a Repertoire share the same document layout).

## Further Notes

- Maintains complete backward compatibility: omitting layout or color arguments in the generator pipeline defaults to 2 columns and `#E65100` orange.
