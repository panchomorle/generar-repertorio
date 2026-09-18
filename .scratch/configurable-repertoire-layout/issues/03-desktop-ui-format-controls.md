# 03: Desktop UI Format Controls and Generation Integration

**What to build:** User interface controls in the desktop application that allow musicians to switch between 1 and 2 columns, view an adaptive usage hint, pick a custom chord color with a discrete swatch button, and compile the Repertoire with their chosen settings. The controls load the user's persisted preferences on launch and auto-save changes. During compilation, the generation worker passes the active layout and color into the engine.

**Blocked by:** 01: Layout Presets and Chord Color in Repertoire Engine, 02: Local Settings Persistence Module.

**Status:** done

- [x] A compact format options row is rendered in the generation panel above the progress bar.
- [x] A segmented button allows toggling between 1 Column and 2 Columns, initialized to the persisted preference.
- [x] A subtle informational hint is displayed explaining that 1 column adapts best to screens/tablets while 2 columns is best for printing.
- [x] A compact square preview button displays the active chord color; clicking it opens the operating system's native color picker dialog.
- [x] Selecting a new color in the dialog updates the preview swatch, saves the preference, and applies it to subsequent generations.
- [x] Changing column layout or chord color immediately persists to local settings.
- [x] Clicking "Generar Repertorio" compiles the document using the selected column layout and chord color.
- [x] The desktop UI remains responsive during generation and color selection.
