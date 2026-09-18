from pathlib import Path
from typing import List, Dict, Any

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from repertorio.transposer import transpose_key, transpose_lines


FONT_NAME = "Consolas"
DEFAULT_COLUMNS = 2
DEFAULT_CHORD_COLOR_HEX = "#E65100"
DEFAULT_CHORD_COLOR = RGBColor(230, 81, 0)  # Vibrant orange
CHORD_COLOR = DEFAULT_CHORD_COLOR           # Backward compatibility
TEXT_COLOR = RGBColor(40, 40, 40)           # Soft dark gray
HEADER_COLOR = RGBColor(20, 20, 20)         # Dark title color
META_COLOR = RGBColor(100, 100, 100)        # Muted gray for metadata

LAYOUT_PRESETS: Dict[int, Dict[str, Any]] = {
    1: {
        "columns": 1,
        "font_size": Pt(10.5),
        "line_spacing": Pt(13.0),
    },
    2: {
        "columns": 2,
        "font_size": Pt(8.5),
        "line_spacing": Pt(10.5),
    },
}


def parse_chord_color(color: Any) -> RGBColor:
    """Safely parse a color representation into an RGBColor instance.
    
    Supports:
      - None (defaults to DEFAULT_CHORD_COLOR)
      - RGBColor instance
      - Tuple/list of (r, g, b) integers in range 0-255
      - Hex string with or without '#' (3 or 6 hex digits)
    Falls back gracefully to DEFAULT_CHORD_COLOR on invalid input.
    """
    if color is None:
        return DEFAULT_CHORD_COLOR

    if isinstance(color, RGBColor):
        return color

    if isinstance(color, (tuple, list)):
        try:
            if len(color) == 3:
                r, g, b = int(color[0]), int(color[1]), int(color[2])
                if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                    return RGBColor(r, g, b)
        except (ValueError, TypeError):
            pass
        return DEFAULT_CHORD_COLOR

    if isinstance(color, str):
        cleaned = color.strip()
        if cleaned.startswith("#"):
            cleaned = cleaned[1:]

        try:
            if len(cleaned) == 3:
                cleaned = "".join(c * 2 for c in cleaned)
            if len(cleaned) == 6:
                r = int(cleaned[0:2], 16)
                g = int(cleaned[2:4], 16)
                b = int(cleaned[4:6], 16)
                return RGBColor(r, g, b)
        except ValueError:
            pass
        return DEFAULT_CHORD_COLOR

    return DEFAULT_CHORD_COLOR


def get_layout_preset(columns: int = 2) -> Dict[str, Any]:
    """Retrieve typography and layout preset for the requested column count.
    
    Defaults to 2-column preset on invalid or unsupported values.
    """
    try:
        col_int = int(columns)
    except (ValueError, TypeError):
        col_int = DEFAULT_COLUMNS

    return LAYOUT_PRESETS.get(col_int, LAYOUT_PRESETS[DEFAULT_COLUMNS])


def _set_section_columns_and_margins(section, num_cols: int = 2, space_pts: int = 720) -> None:
    """Set column layout and tight 0.5 inch margins on a Word section."""
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)

    sectPr = section._sectPr
    cols = sectPr.xpath("./w:cols")
    if cols:
        cols[0].set(qn("w:num"), str(num_cols))
        cols[0].set(qn("w:space"), str(space_pts))
    else:
        cols_elem = OxmlElement("w:cols")
        cols_elem.set(qn("w:num"), str(num_cols))
        cols_elem.set(qn("w:space"), str(space_pts))
        sectPr.append(cols_elem)


def build_document(
    songs: List[Dict[str, Any]],
    output_path: Path | str,
    columns: int = 2,
    chord_color: Any = None,
) -> None:
    """Build a professional Word document containing the provided songs formatted with layout presets."""
    preset = get_layout_preset(columns)
    resolved_chord_color = parse_chord_color(chord_color)

    doc = docx.Document()

    for i, song in enumerate(songs):
        # First song uses default section; subsequent songs start on a new page with their own section
        if i == 0:
            section = doc.sections[0]
        else:
            section = doc.add_section(WD_SECTION.NEW_PAGE)

        _set_section_columns_and_margins(section, num_cols=preset["columns"], space_pts=720)

        # Song Title & Artist header
        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(2)
        r_title = p_title.add_run(f"{song.get('title', 'Canción')} - {song.get('artist', 'Artista')}")
        r_title.bold = True
        r_title.font.name = FONT_NAME
        r_title.font.size = Pt(12)
        r_title.font.color.rgb = HEADER_COLOR

        semitones = int(song.get("semitones", 0))
        base_key = song.get("key")

        # Optional Key (Tom) and Capo metadata line
        meta_items = []
        if base_key:
            if semitones != 0:
                transposed_key = transpose_key(base_key, semitones)
                meta_items.append(f"Tono: {transposed_key} (Original: {base_key})")
            else:
                meta_items.append(f"Tono: {base_key}")
        elif semitones != 0:
            sign = f"+{semitones}" if semitones > 0 else str(semitones)
            meta_items.append(f"Tono: Transpuesto ({sign})")

        if song.get("capo") and song["capo"] != "N/A":
            meta_items.append(f"Capo: {song['capo']}")

        if meta_items:
            p_meta = doc.add_paragraph()
            p_meta.paragraph_format.space_before = Pt(0)
            p_meta.paragraph_format.space_after = Pt(6)
            r_meta = p_meta.add_run(" | ".join(meta_items))
            r_meta.italic = True
            r_meta.font.name = FONT_NAME
            r_meta.font.size = preset["font_size"]
            r_meta.font.color.rgb = META_COLOR

        # Render song lines (chords & lyrics)
        raw_lines = song.get("lines", [])
        lines = transpose_lines(raw_lines, semitones) if semitones != 0 else raw_lines
        for line_tokens in lines:
            line_text = "".join(t["text"] for t in line_tokens)

            p_line = doc.add_paragraph()
            p_line.paragraph_format.line_spacing = preset["line_spacing"]

            if not line_text.strip():
                # Empty line separating stanzas
                p_line.paragraph_format.space_before = Pt(0)
                p_line.paragraph_format.space_after = Pt(4)
                continue

            # Section marker check, e.g. [Intro], [Estribillo], [Refrão]
            is_section_header = line_text.strip().startswith("[") and line_text.strip().endswith("]")

            if is_section_header:
                p_line.paragraph_format.space_before = Pt(4)
                p_line.paragraph_format.space_after = Pt(1)
            else:
                p_line.paragraph_format.space_before = Pt(0)
                p_line.paragraph_format.space_after = Pt(0)

            for token in line_tokens:
                text = token["text"]
                if not text:
                    continue
                run = p_line.add_run(text)
                run.font.name = FONT_NAME
                run.font.size = preset["font_size"]

                if token.get("is_chord"):
                    run.bold = True
                    run.font.color.rgb = resolved_chord_color
                elif is_section_header:
                    run.bold = True
                    run.font.color.rgb = META_COLOR
                else:
                    run.bold = False
                    run.font.color.rgb = TEXT_COLOR

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))

