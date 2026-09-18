# Song Overrides and Preview Editing in Setlist

To allow musicians to correct lyrics, adjust chord voicings, or delete unwanted sections (such as excessive guitar tabs or intros) without modifying the original CifraClub cache, we introduced Setlist-level Song Overrides and a direct modal editor.

1. **Setlist-Level Override**:
   - Edits are saved as a `Song Override` tied exclusively to that Song's entry in the Setlist.
   - The global cache in `.cache_cifras/songs/` remains immutable.
   - Songs with custom edits display a clear badge (`[✏️ Editada]`) in the Setlist UI and provide a "Restaurar original" action to roll back changes.

2. **Harmonic Model and Transposition**:
   - The modal editor presents chords in the active transposed key (WYSIWYG) so musicians edit what they hear and play.
   - The editor includes live decrement (`[-]`) and increment (`[+]`) transposition controls synchronized with the Setlist state.
   - The cumulative semitone offset relative to CifraClub's original key is preserved, ensuring that Word metadata (`Tono: A (Original: G)`) and downstream transposition adjustments remain mathematically consistent.

3. **Compilation Pipeline**:
   - During Repertoire generation, `generator.py` prioritizes the Song Override content when present, bypassing the cached CifraClub body while continuing to apply the configured semitone transposition.
