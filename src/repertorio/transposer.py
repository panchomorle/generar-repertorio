import re
from typing import List, Dict, Any, Optional

NOTE_TO_PITCH: Dict[str, int] = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}

PITCH_TO_NOTE_MAJOR: List[str] = [
    "C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"
]

PITCH_TO_NOTE_MINOR: List[str] = [
    "C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"
]

CHORD_PATTERN = re.compile(
    r"^([A-G][#b]?)([^/]*)(?:/([A-G][#b]?)(.*))?$"
)


def _shift_note(note: str, semitones: int, is_minor: bool = False, prefer_sharps: Optional[bool] = None) -> str:
    """Shift a single note by a number of semitones."""
    if note not in NOTE_TO_PITCH:
        return note

    current_pitch = NOTE_TO_PITCH[note]
    new_pitch = (current_pitch + semitones) % 12

    if prefer_sharps is None:
        if "#" in note:
            prefer_sharps = True
        elif "b" in note:
            prefer_sharps = False

    if prefer_sharps is True:
        table = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return table[new_pitch]
    elif prefer_sharps is False:
        table = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
        return table[new_pitch]

    # Contextual default
    if is_minor:
        return PITCH_TO_NOTE_MINOR[new_pitch]
    return PITCH_TO_NOTE_MAJOR[new_pitch]


def transpose_chord(chord_str: str, semitones: int) -> str:
    """Transpose a chord string (e.g. 'Bm', 'Gmaj7', 'D/F#') by semitones."""
    if not chord_str or not chord_str.strip() or semitones == 0:
        return chord_str

    match = CHORD_PATTERN.match(chord_str.strip())
    if not match:
        return chord_str

    root_note = match.group(1)
    quality = match.group(2) or ""
    bass_note = match.group(3)
    bass_mod = match.group(4) or ""

    if root_note not in NOTE_TO_PITCH:
        return chord_str

    is_minor = quality.startswith("m") and not quality.startswith("maj")

    original_has_sharp = ("#" in root_note) or (bass_note is not None and "#" in bass_note)
    original_has_flat = ("b" in root_note) or (bass_note is not None and "b" in bass_note)
    prefer_sharps = True if original_has_sharp else (False if original_has_flat else None)

    new_root = _shift_note(root_note, semitones, is_minor=is_minor, prefer_sharps=prefer_sharps)

    result = f"{new_root}{quality}"

    if bass_note:
        if bass_note in NOTE_TO_PITCH:
            bass_prefer_sharp = prefer_sharps
            if new_root in {"E", "B", "A", "D", "G", "F#", "C#"}:
                bass_prefer_sharp = True
            new_bass = _shift_note(bass_note, semitones, is_minor=False, prefer_sharps=bass_prefer_sharp)
            result = f"{result}/{new_bass}{bass_mod}"
        else:
            result = f"{result}/{bass_note}{bass_mod}"

    return result


def transpose_key(key_str: Optional[str], semitones: int) -> Optional[str]:
    """Transpose a musical key string (e.g. 'Bm', 'C', 'F#') by semitones."""
    if not key_str:
        return key_str
    if semitones == 0:
        return key_str

    return transpose_chord(key_str, semitones)


def transpose_lines(lines: List[List[Dict[str, Any]]], semitones: int) -> List[List[Dict[str, Any]]]:
    """Transpose all chord tokens in tokenized lines by semitones."""
    if semitones == 0:
        return lines

    transposed_lines: List[List[Dict[str, Any]]] = []
    for line in lines:
        new_line: List[Dict[str, Any]] = []
        for token in line:
            text = token.get("text", "")
            is_chord = token.get("is_chord", False)
            if is_chord and text:
                new_line.append({
                    "text": transpose_chord(text, semitones),
                    "is_chord": True
                })
            else:
                new_line.append(dict(token))
        transposed_lines.append(new_line)

    return transposed_lines
