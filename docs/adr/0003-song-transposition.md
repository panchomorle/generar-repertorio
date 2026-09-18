# Song Transposition and Key Display in Setlist

To allow musicians to adjust songs to their vocal or instrumental range without leaving the application, we introduced song transposition and key display into the Setlist and Repertoire compilation pipeline.

1. **Key Extraction**: CifraClub's modern HTML renders the musical key in a button with `data-anchor="--chord-tone"` within the key container. Songs added to the Setlist have their base key resolved immediately (via local cache or background fetch).
2. **UI Controls**: Each Song in the Setlist GUI provides relative semitone decrement (`[-]`) and increment (`[+]`) controls. The UI dynamically computes and displays the resulting transposed key alongside the semitone offset.
3. **Harmonic Engine**: A lightweight musical transposition module parses chord tokens (handling root note, accidentals, chord quality, and slash chord bass notes) and shifts them by the selected semitone offset, using standard enharmonic conventions.
4. **Repertoire Output**: In the generated Word (.docx) document, chord lines are rendered in the transposed pitch, and the header displays the transposed key while preserving the original key reference when an offset is applied (e.g. `Tono: C#m (Original: Bm)`).
