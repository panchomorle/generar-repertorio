# Configurable Repertoire Layout and Adaptive Typography

To allow musicians to optimize the compiled Repertoire for digital performance stands (tablets, laptops) as well as traditional printed sheets, we introduced configurable document layouts, automatic typography presets, customizable chord colors, and local settings persistence.

1. **Adaptive Column Layout and Typography**:
   - The document compiler supports `num_cols = 1` and `num_cols = 2`.
   - Typography metrics are automatically coupled to column counts:
     - **1 Column (Screen/Tablet)**: 10.5 pt font with 13 pt line spacing, maximizing readability from performance distance.
     - **2 Columns (Print)**: 8.5 pt font with 10.5 pt line spacing, preserving compact multi-bar chord lines within narrow column boundaries.
   - Decoupling column selection from manual font sliders prevents users from accidentally breaking multi-column layouts with oversized text.

2. **Decoupled Chord Color Customization**:
   - The desktop UI provides a discrete preview swatch button that opens the native OS color chooser dialog (`tkinter.colorchooser.askcolor`).
   - Default color remains brand orange (`#E65100`), with full freedom to choose solid black (`#000000`) for crisp contrast on monochrome laser printers.
   - The chord color configuration is passed directly through the generation pipeline into OpenXML paragraph runs.

3. **Application-Level Local Settings Persistence**:
   - Formatting preferences (`columns` and `chord_color`) are saved to `.cache_cifras/settings.json`.
   - Settings are decoupled from the `Setlist` domain entity, keeping setlists focused purely on song selections and musical keys while enabling users to export the same setlist for different media targets without altering the setlist file.
