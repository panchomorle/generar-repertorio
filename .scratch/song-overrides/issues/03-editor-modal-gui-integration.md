# 03: Desktop Editor Modal and Setlist UI Integration

**What to build:** An interactive desktop editing experience in the application. Clicking on any song row in the Setlist opens a modal editor displaying the song's chords and lyrics in monospace font at the currently transposed pitch. The modal provides live transposition controls (`[-]` and `[+]`) synchronized with the song's setlist state, a "Guardar cambios" button to commit the override, and a "Restaurar original" button to revert. In the main Setlist view, songs with custom overrides display a distinct badge (`[✏️ Editada]`) for clear visibility.

**Blocked by:** 02: Setlist Song Override and Generator Core

**Status:** ready-for-agent

- [ ] Clicking on a song row in the Setlist GUI opens a modal editor dialog.
- [ ] The editor loads and displays the song's chord sheet in monospace font at its currently transposed key (WYSIWYG).
- [ ] The editor header displays song title, artist, current key, and live `[-]` and `[+]` transposition buttons that update the chord sheet text in real time.
- [ ] The cumulative semitone offset from CifraClub's original key is tracked and preserved when editing and saving.
- [ ] Clicking "Guardar cambios" parses the text into an override, commits it to the Setlist, triggers autosave, closes the modal, and renders the `[✏️ Editada]` badge on the song row.
- [ ] Clicking "Restaurar original" clears the override, reverts the song to the CifraClub source, removes the edit badge, and refreshes the view.
- [ ] Closing the modal via "Cerrar", cancel, or Escape without saving leaves the previous state unchanged.
- [ ] The UI remains responsive and does not freeze while opening or saving songs.
