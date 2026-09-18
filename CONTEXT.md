# Repertoire Generator

Generates a formatted 2-column chord songbook (.docx) from songs fetched directly from CifraClub.

## Language

**Setlist**:
The ordered, persistent collection of curated songs saved locally and used to compile a repertoire.
_Avoid_: playlist, queue, txt list

**Song**:
A chord sheet entity resolved from CifraClub, containing artist, title, dns, url path, detected key, and semitone transposition offset.
_Avoid_: track, cifra, tema

**Transposition**:
The semitone offset applied to a Song's chords and key when compiling the Repertoire.
_Avoid_: cambio de tono, pitch shift

**Repertoire**:
The final compiled Word (.docx) document containing formatted two-column chord sheets and page breaks for each song in the setlist.
_Avoid_: cancionero, book, output file

**Song Override**:
A Setlist-level customized chord sheet and metadata that overrides the cached CifraClub content for a Song without mutating the underlying cache.
_Avoid_: custom song, local patch, edited track
