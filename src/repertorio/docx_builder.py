from pathlib import Path
from typing import List, Dict, Any

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


FONT_NAME = "Consolas"
CHORD_COLOR = RGBColor(230, 81, 0)  # Vibrant orange
TEXT_COLOR = RGBColor(40, 40, 40)    # Soft dark gray
HEADER_COLOR = RGBColor(20, 20, 20)  # Dark title color
META_COLOR = RGBColor(100, 100, 100) # Muted gray for metadata


def _set_section_columns_and_margins(section, num_cols: int = 2, space_pts: int = 720) -> None:
    """Set 2-column layout and tight 0.5 inch margins on a Word section."""
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


def build_document(songs: List[Dict[str, Any]], output_path: Path | str) -> None:
    """Build a professional 2-column Word document containing the provided songs."""
    doc = docx.Document()

    for i, song in enumerate(songs):
        # First song uses default section; subsequent songs start on a new page with their own section
        if i == 0:
            section = doc.sections[0]
        else:
            section = doc.add_section(WD_SECTION.NEW_PAGE)

        _set_section_columns_and_margins(section, num_cols=2, space_pts=720)

        # Song Title & Artist header
        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(2)
        r_title = p_title.add_run(f"{song.get('title', 'Canción')} - {song.get('artist', 'Artista')}")
        r_title.bold = True
        r_title.font.name = FONT_NAME
        r_title.font.size = Pt(12)
        r_title.font.color.rgb = HEADER_COLOR

        # Optional Key (Tom) and Capo metadata line
        meta_items = []
        if song.get("key"):
            meta_items.append(f"Tono: {song['key']}")
        if song.get("capo") and song["capo"] != "N/A":
            meta_items.append(f"Capo: {song['capo']}")

        if meta_items:
            p_meta = doc.add_paragraph()
            p_meta.paragraph_format.space_before = Pt(0)
            p_meta.paragraph_format.space_after = Pt(6)
            r_meta = p_meta.add_run(" | ".join(meta_items))
            r_meta.italic = True
            r_meta.font.name = FONT_NAME
            r_meta.font.size = Pt(8.5)
            r_meta.font.color.rgb = META_COLOR

        # Render song lines (chords & lyrics)
        lines = song.get("lines", [])
        for line_tokens in lines:
            line_text = "".join(t["text"] for t in line_tokens)

            p_line = doc.add_paragraph()
            p_line.paragraph_format.line_spacing = Pt(10.5)

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
                run.font.size = Pt(8.5)

                if token.get("is_chord"):
                    run.bold = True
                    run.font.color.rgb = CHORD_COLOR
                elif is_section_header:
                    run.bold = True
                    run.font.color.rgb = META_COLOR
                else:
                    run.bold = False
                    run.font.color.rgb = TEXT_COLOR

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
