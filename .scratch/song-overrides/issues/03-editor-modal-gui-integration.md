# 03: Desktop Editor Modal and Setlist UI Integration

**What to build:** An interactive desktop editing experience in the application. Clicking on any song row in the Setlist opens a modal editor displaying the song's chords and lyrics in monospace font at the currently transposed pitch. The modal provides live transposition controls (`[-]` and `[+]`) synchronized with the song's setlist state, a "Guardar cambios" button to commit the override, and a "Restaurar original" button to revert. In the main Setlist view, songs with custom overrides display a distinct badge (`[✏️ Editada]`) for clear visibility.

**Blocked by:** 02: Setlist Song Override and Generator Core

**Status:** resolved

- [x] Clicking on a song row in the Setlist GUI opens a modal editor dialog.
- [x] The editor loads and displays the song's chord sheet in monospace font at its currently transposed key (WYSIWYG).
- [x] The editor header displays song title, artist, current key, and live `[-]` and `[+]` transposition buttons that update the chord sheet text in real time.
- [x] The cumulative semitone offset from CifraClub's original key is tracked and preserved when editing and saving.
- [x] Clicking "Guardar cambios" parses the text into an override, commits it to the Setlist, triggers autosave, closes the modal, and renders the `[✏️ Editada]` badge on the song row.
- [x] Clicking "Restaurar original" clears the override, reverts the song to the CifraClub source, removes the edit badge, and refreshes the view.
- [x] Closing the modal via "Cerrar", cancel, or Escape without saving leaves the previous state unchanged.
- [x] The UI remains responsive and does not freeze while opening or saving songs.

## Comments

- Implemented `SongEditModal` in `src/repertorio/ui/editor.py` (`CTkToplevel`) featuring monospace text editor (`Consolas`), live header transposition controls (`[-]` and `[+]`), WYSIWYG transposed display, and inverse normalization on save.
- Integrated modal launching on song row click and edit button in `RepertoireApp.render_setlist` (`src/repertorio/ui/app.py`).
- Added persistent `[✏️ Editada]` badge on modified setlist rows and "Restaurar original" rollback dialog.
- Non-blocking background fetch with `queue.Queue` prevents GUI freezes for uncached songs.
- Added comprehensive unit and integration tests in `tests/test_ui_editor.py`.
