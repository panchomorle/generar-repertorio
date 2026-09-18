import re
from typing import List, Dict, Any, Tuple

from repertorio.cleaner import is_tab_line

# Regex matching a valid chord token in monospace text sheets.
# Requires non-alphanumeric boundaries to avoid matching lyrics words (e.g. 'Amor', 'De', 'Ella').
CHORD_REGEX = re.compile(
    r"(?<![A-Za-z0-9])"
    r"([A-G][#b]?"
    r"(?:"
        r"(?:maj|Maj|min|m|M|dim|aug|sus|add|alt|\+|°|º)?"
        r"(?:[0-9]{1,2})?"
        r"(?:M)?"
        r"(?:(?:maj|Maj|min|m|dim|aug|sus|add|alt)?[0-9]*)*"
        r"(?:[b#+-][0-9]+)*"
        r"(?:\([a-zA-Z0-9#b+/\-,\s]+\))*"
    r")"
    r"(?:/[A-G][#b]?(?:[0-9]+)?)?"
    r")"
    r"(?![A-Za-z0-9])"
)

# Common structural section keywords in Portuguese and Spanish chord sheets
KNOWN_SECTION_KEYWORDS = {
    "intro", "solo", "refrão", "refrao", "coro", "estribillo", "verso",
    "estrofa", "bridge", "puente", "outro", "interludio", "inter",
    "final", "pre-coro", "pos-refrão", "riff"
}


def is_chord_token(token: str) -> bool:
    """Check if a single string represents a valid musical chord notation."""
    if not token or not token.strip():
        return False
    return bool(CHORD_REGEX.fullmatch(token.strip()))


def _get_bracket_ranges(line: str) -> List[Tuple[int, int]]:
    """Return start and end spans of bracketed section tags like [Intro] or [Solo]."""
    return [(m.start(), m.end()) for m in re.finditer(r"\[[^\]]*\]", line)]


def _is_inside_ranges(start: int, end: int, ranges: List[Tuple[int, int]]) -> bool:
    """Check if a span lies entirely inside any of the bracket ranges."""
    return any(r_start <= start and end <= r_end for r_start, r_end in ranges)


def find_chord_spans(line: str) -> List[Tuple[int, int]]:
    """Locate all chord occurrences and character spans in a line, ignoring section tags."""
    bracket_ranges = _get_bracket_ranges(line)
    chord_spans: List[Tuple[int, int]] = []
    for m in CHORD_REGEX.finditer(line):
        if not _is_inside_ranges(m.start(), m.end(), bracket_ranges):
            chord_spans.append((m.start(), m.end()))
    return chord_spans


def is_section_header_line(line: str) -> bool:
    """Determine if a line is exclusively a section label like [Intro] or [Estribillo]."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("[") and stripped.endswith("]"):
        return True
    if stripped.startswith("(") and stripped.endswith(")"):
        inner = stripped[1:-1].strip().lower()
        if inner in KNOWN_SECTION_KEYWORDS:
            return True
    return False


def is_chord_line(line: str) -> bool:
    """Determine whether a line is a chord line rather than lyrics or section headers."""
    stripped = line.strip()
    if not stripped or is_tab_line(line) or is_section_header_line(line):
        return False

    chord_spans = find_chord_spans(line)
    if not chord_spans:
        return False

    # Mask out chord spans to inspect remaining text
    masked = list(line)
    for start, end in chord_spans:
        for i in range(start, end):
            masked[i] = " "

    # Mask section brackets [ ... ]
    for m in re.finditer(r"\[[^\]]*\]", line):
        for i in range(m.start(), m.end()):
            masked[i] = " "

    # Mask repeat markers (2x), x2, etc.
    for m in re.finditer(r"\([0-9]+x\)|[0-9]+x|x[0-9]+|\(x[0-9]+\)|\(?bis\)?", line, re.I):
        for i in range(m.start(), m.end()):
            masked[i] = " "

    # Mask common section prefixes with colons, e.g. 'Intro:', 'Solo:'
    for m in re.finditer(r"\b(intro|solo|riff|inter|interludio|final|outro|verso|coro|refr[aã]o):", line, re.I):
        for i in range(m.start(), m.end()):
            masked[i] = " "

    remainder = "".join(masked)
    remaining_words = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑãõçêôà]+", remainder)

    chord_count = len(chord_spans)
    # A single isolated letter (e.g. 'A') surrounded by lyrics words is part of the lyrics
    if chord_count == 1 and len(remaining_words) > 0:
        return False

    total_meaningful = chord_count + len(remaining_words)
    if total_meaningful == 0:
        return False

    return (chord_count / total_meaningful) >= 0.6


def tokenize_chord_line(line: str) -> List[Dict[str, Any]]:
    """Tokenize a chord line into chords (is_chord=True) and spacing/delimiters (is_chord=False)."""
    chord_spans = find_chord_spans(line)
    tokens: List[Dict[str, Any]] = []
    last_idx = 0

    for start, end in chord_spans:
        if start > last_idx:
            tokens.append({"text": line[last_idx:start], "is_chord": False})
        tokens.append({"text": line[start:end], "is_chord": True})
        last_idx = end

    if last_idx < len(line):
        tokens.append({"text": line[last_idx:], "is_chord": False})

    return tokens


def parse_text_to_lines(text: str) -> List[List[Dict[str, Any]]]:
    """Parse monospace plain text into structured line tokens for document generation.

    Distinguishes chord lines from lyrics, preserves indentation and column offsets,
    and flags recognized chords for downstream harmonic transposition.
    """
    if not text:
        return []

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = normalized.split("\n")
    lines: List[List[Dict[str, Any]]] = []

    for line in raw_lines:
        if not line.strip():
            lines.append([{"text": "", "is_chord": False}])
        elif is_tab_line(line):
            lines.append([{"text": line, "is_chord": False}])
        elif is_section_header_line(line):
            lines.append([{"text": line, "is_chord": False}])
        elif is_chord_line(line):
            lines.append(tokenize_chord_line(line))
        else:
            lines.append([{"text": line, "is_chord": False}])

    return lines


def format_lines_to_text(lines: List[List[Dict[str, Any]]]) -> str:
    """Format structured tokenized lines back into clean monospace text for editing."""
    return "\n".join("".join(t.get("text", "") for t in line) for line in lines)
