# Spec: Song Transposition and Key Display in Setlist

Status: completed

## Problem Statement

Músicos y vocalistas frecuentemente necesitan transportar canciones a diferentes tonalidades para adecuarlas a su rango vocal o comodidades de digitación. Actualmente:
1. El Setlist no visualiza la tonalidad original de las canciones añadidas.
2. CifraClub actualizó su HTML y el extractor de tono actual falla (devuelve null).
3. No existen controles en la interfaz ni en el pipeline para modificar la tonalidad de una canción antes de generar el Repertoire Word (.docx).

## Solution

1. **Reparar extracción de tono**: Actualizar el scraper para detectar la tonalidad actual de CifraClub (`data-anchor="--chord-tone"` y contenedores con prefijo "Tom:").
2. **Tonalidad en Setlist**: Resolver y persistir la tonalidad (`key`) al agregar cada Song al Setlist (leyendo de caché o consultando en background sin congelar la UI).
3. **Controles de transposición por semitonos**: Proveer botones `[-]` y `[+]` por cada fila del Setlist que ajusten el offset en semitonos (ej. `+2`) y muestren la tonalidad resultante en vivo (ej. `Bm -> C#m (+2)`).
4. **Módulo armónico de transposición (`transposer.py`)**: Parsear acordes simples y compuestos (raíz, alteraciones `#`/`b`, sufijos/calidades `m`, `7`, `maj7`, etc., y bajos invertidos tipo `D/F#`) y transportar los tokens respetando las posiciones y espacios originales.
5. **Encabezado y acordes en Repertoire (.docx)**:
   - Al generar el documento Word, transponer los acordes según el offset de cada Song.
   - Si la Song fue transpuesta, mostrar en el encabezado de metadatos: `Tono: <Tono_Transpuesto> (Original: <Tono_Original>)`.
   - Si no fue transpuesta, mantener `Tono: <Tono_Original>`.

## User Stories

1. Como usuario, quiero ver la tonalidad de cada canción directamente en la lista del Setlist para saber en qué tono está cada tema antes de compilar.
2. Como músico, quiero poder subir o bajar semitonos con botones `+` y `-` en cada canción del Setlist para acomodarla a la voz de la banda.
3. Como usuario, quiero ver el tono resultante actualizado en tiempo real en la fila de la canción a medida que presiono `+` o `-`.
4. Como lector del cancionero, quiero que el Word generado contenga los acordes transpuestos correctamente en todas las secciones del tema.
5. Como músico en vivo, quiero que el encabezado de cada tema en el Word aclare la tonalidad efectiva y la tonalidad original de referencia si fue transpuesta.
6. Como usuario, quiero que la tonalidad y el desplazamiento por semitonos se guarden automáticamente en el Setlist (`setlist.json`) y se conserven al exportar/importar listas.

## Implementation Decisions

- **Pipeline de transposición**:
  - `src/repertorio/transposer.py`:
    - Tablas cromáticas para sostenidos y bemoles.
    - Función `transpose_chord(chord_str: str, semitones: int) -> str` que soporta acordes con bajo (slash chords).
    - Función `transpose_lines(lines: List[List[Dict[str, Any]]], semitones: int) -> List[List[Dict[str, Any]]]`.
    - Función `transpose_key(key_str: str, semitones: int) -> str`.
- **Setlist Data Model**:
  - Cada item de `songs` en `Setlist` admite `key` (str opcional) y `semitones` (int, default 0).
  - Métodos `set_song_key(index, key)` y `transpose_song(index, delta)`.
- **Desktop UI**:
  - Al agregar una canción, si no tiene `key`, lanzar un hilo rápido de resolución (caché o scraper) que actualice el label de la fila una vez obtenido.
  - Fila del Setlist: mostrar badge de tono `[Bm]` (o `[C#m (+2)]`), botón `[-]`, botón `[+]`.
- **Generador y Docx Builder**:
  - `generate_from_songs` pasa `song.get("semitones", 0)` a `docx_builder`.
  - `build_document` aplica transposición a los tokens de acordes y ajusta el string de metadatos `Tono: ...`.

## Testing Decisions

- Test unitario completo en `tests/test_transposer.py` para acordes mayores, menores, séptimas, tensiones y slash chords (ej: `D/F#` + 2 = `E/G#`, `Bb` - 1 = `A`, `G#m` + 1 = `Am`).
- Test de persistencia en `tests/test_setlist.py` verificando que `key` y `semitones` se conserven en `add_song`, `export_to_file`, e `import_from_file`.
- Test de integración en `tests/test_generator.py` verificando que un tema transpuesto genere el docx con acordes y encabezado correctos.
