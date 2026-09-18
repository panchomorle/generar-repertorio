import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import docx
from docx.shared import RGBColor, Pt
import pytest

from repertorio.generator import generate_repertoire
from repertorio.docx_builder import (
    DEFAULT_COLUMNS,
    DEFAULT_CHORD_COLOR,
    DEFAULT_CHORD_COLOR_HEX,
    LAYOUT_PRESETS,
    parse_chord_color,
    get_layout_preset,
    build_document,
)


MOCK_SOLR_RESPONSE = {
    "response": {
        "numFound": 1,
        "docs": [
            {
                "art": "Soda Stereo",
                "dns": "soda-stereo",
                "txt": "De Música Ligera",
                "url": "de-musica-ligera",
            }
        ],
    }
}

MOCK_HTML_PAGE = """<!DOCTYPE html>
<html>
<body>
<h1>De Música Ligera</h1>
<pre class="_crVx" data-chord-content="true">
<div class="kvMV">[Intro] <b>Bm</b>  <b>G</b>  <b>D</b>  <b>A</b>
E|----------------------------|
B|----------------------------|
G|----------------------------|
D|----------------------------|
A|----------------------------|
E|----------------------------|
</div>
<div class="kvMV"><b>Bm</b>        <b>G</b>  <b>D</b>
Ella durmio
      <b>A</b>           <b>Bm</b>   <b>G</b>  <b>D</b>  <b>A</b>
Al calor de las masas
</div>
</pre>
</body>
</html>
"""


@pytest.fixture
def temp_workspace(tmp_path):
    songs_file = tmp_path / "canciones.txt"
    songs_file.write_text("de musica ligera\n", encoding="utf-8")
    output_docx = tmp_path / "repertorio.docx"
    cache_dir = tmp_path / ".cache_cifras"
    return {
        "songs_file": songs_file,
        "output_docx": output_docx,
        "cache_dir": cache_dir,
    }


def test_generator_end_to_end(temp_workspace):
    songs_file = temp_workspace["songs_file"]
    output_docx = temp_workspace["output_docx"]
    cache_dir = temp_workspace["cache_dir"]

    # Mock HTTP calls
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_solr_resp = MagicMock()
        mock_solr_resp.read.return_value = json.dumps(MOCK_SOLR_RESPONSE).encode("utf-8")
        mock_solr_resp.__enter__.return_value = mock_solr_resp

        mock_page_resp = MagicMock()
        mock_page_resp.read.return_value = MOCK_HTML_PAGE.encode("utf-8")
        mock_page_resp.__enter__.return_value = mock_page_resp

        mock_urlopen.side_effect = [mock_solr_resp, mock_page_resp]

        # 1. First execution: should query network and create cache
        stats = generate_repertoire(songs_file, output_docx, cache_dir=cache_dir)

        assert stats["total"] == 1
        assert stats["downloaded"] == 1
        assert stats["cached"] == 0
        assert stats["failed"] == 0
        assert mock_urlopen.call_count == 2

    # Verify output file exists
    assert output_docx.exists()

    # Verify cache files: 1 in songs/ and 1 index.json
    songs_dir = cache_dir / "songs"
    cache_files = list(songs_dir.glob("*.json"))
    assert len(cache_files) == 1
    with open(cache_files[0], encoding="utf-8") as f:
        cached_data = json.load(f)
    assert cached_data["artist"] == "Soda Stereo"
    assert cached_data["title"] == "De Música Ligera"

    index_file = cache_dir / "index.json"
    assert index_file.exists()
    with open(index_file, encoding="utf-8") as f:
        index_data = json.load(f)
    assert index_data.get("de musica ligera") == "soda-stereo_de-musica-ligera"

    # Verify DOCX structure
    doc = docx.Document(output_docx)
    section = doc.sections[0]

    # 2 columns configuration check
    cols = section._sectPr.xpath("./w:cols")
    assert len(cols) > 0
    assert cols[0].get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num") == "2"

    all_text = "\n".join([p.text for p in doc.paragraphs])
    # Should include title and lyrics
    assert "De Música Ligera" in all_text
    assert "Soda Stereo" in all_text
    assert "Ella durmio" in all_text

    # Tablature lines must be filtered out
    assert "E|----------------------------|" not in all_text
    assert "A|----------------------------|" not in all_text

    # Verify chord styling (Consolas, bold, orange RGB(230, 81, 0))
    chord_runs = []
    for p in doc.paragraphs:
        for r in p.runs:
            if r.bold and r.font.color and r.font.color.rgb == RGBColor(230, 81, 0):
                chord_runs.append(r.text)

    assert "Bm" in chord_runs
    assert "G" in chord_runs
    assert "D" in chord_runs
    assert "A" in chord_runs

    # 2. Second execution: should use cache, zero network calls
    with patch("urllib.request.urlopen") as mock_urlopen_2:
        stats_2 = generate_repertoire(songs_file, output_docx, cache_dir=cache_dir)
        assert stats_2["total"] == 1
        assert stats_2["downloaded"] == 0
        assert stats_2["cached"] == 1
        assert stats_2["failed"] == 0
        assert mock_urlopen_2.call_count == 0


def test_generate_from_songs(temp_workspace):
    from repertorio.generator import generate_from_songs

    output_docx = temp_workspace["output_docx"]
    cache_dir = temp_workspace["cache_dir"]
    songs = [
        {"artist": "Soda Stereo", "title": "De Música Ligera", "dns": "soda-stereo", "url": "de-musica-ligera"}
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_page_resp = MagicMock()
        mock_page_resp.read.return_value = MOCK_HTML_PAGE.encode("utf-8")
        mock_page_resp.__enter__.return_value = mock_page_resp
        mock_urlopen.return_value = mock_page_resp

        progress_calls = []
        def on_progress(cur, tot, msg):
            progress_calls.append((cur, tot, msg))

        stats = generate_from_songs(songs, output_docx, cache_dir=cache_dir, progress_callback=on_progress)
        assert stats["total"] == 1
        assert stats["downloaded"] == 1
        assert stats["failed"] == 0
        assert len(progress_calls) >= 2
        assert output_docx.exists()


def test_generate_from_songs_with_transposition(temp_workspace):
    from repertorio.generator import generate_from_songs

    output_docx = temp_workspace["output_docx"]
    cache_dir = temp_workspace["cache_dir"]
    songs = [
        {
            "artist": "Soda Stereo",
            "title": "De Música Ligera",
            "dns": "soda-stereo",
            "url": "de-musica-ligera",
            "key": "Bm",
            "semitones": 2,
        }
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_page_resp = MagicMock()
        mock_page_resp.read.return_value = MOCK_HTML_PAGE.encode("utf-8")
        mock_page_resp.__enter__.return_value = mock_page_resp
        mock_urlopen.return_value = mock_page_resp

        stats = generate_from_songs(songs, output_docx, cache_dir=cache_dir)
        assert stats["total"] == 1
        assert stats["downloaded"] == 1

        doc = docx.Document(output_docx)
        all_text = "\n".join([p.text for p in doc.paragraphs])
        # Transposed key with original reference
        assert "Tono: C#m (Original: Bm)" in all_text

        # Transposed chords: Bm (+2) -> C#m, G (+2) -> A, D (+2) -> E, A (+2) -> B
        chord_runs = []
        for p in doc.paragraphs:
            for r in p.runs:
                if r.bold and r.font.color and r.font.color.rgb == RGBColor(230, 81, 0):
                    chord_runs.append(r.text)

        assert "C#m" in chord_runs
        assert "A" in chord_runs
        assert "E" in chord_runs
        assert "B" in chord_runs
        # Original chords should not be present
        assert "Bm" not in chord_runs


def test_generate_from_songs_with_override(temp_workspace):
    from repertorio.generator import generate_from_songs
    from repertorio.parser import parse_text_to_lines

    output_docx = temp_workspace["output_docx"]
    cache_dir = temp_workspace["cache_dir"]

    custom_chord_sheet = (
        "[Intro] Em  C  G  D\n"
        "\n"
        "Em        C\n"
        "Custom modified lyrics line\n"
        "      D           Em\n"
        "Another custom arranged line"
    )
    override_lines = parse_text_to_lines(custom_chord_sheet)

    songs = [
        {
            "artist": "Soda Stereo",
            "title": "De Música Ligera",
            "dns": "soda-stereo",
            "url": "de-musica-ligera",
            "key": "Em",
            "semitones": 0,
            "override": {
                "lines": override_lines,
                "is_modified": True,
            },
        }
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        stats = generate_from_songs(songs, output_docx, cache_dir=cache_dir)
        # Should not make any network requests
        assert mock_urlopen.call_count == 0
        assert stats["total"] == 1
        assert stats["downloaded"] == 0
        assert stats["cached"] == 1
        assert stats["failed"] == 0

    assert output_docx.exists()
    doc = docx.Document(output_docx)
    all_text = "\n".join([p.text for p in doc.paragraphs])

    # Should contain custom lyrics from override, NOT CifraClub original
    assert "Custom modified lyrics line" in all_text
    assert "Another custom arranged line" in all_text
    assert "Ella durmio" not in all_text

    # Verify custom chords are styled with bold orange
    chord_runs = []
    for p in doc.paragraphs:
        for r in p.runs:
            if r.bold and r.font.color and r.font.color.rgb == RGBColor(230, 81, 0):
                chord_runs.append(r.text)

    assert "Em" in chord_runs
    assert "C" in chord_runs
    assert "G" in chord_runs
    assert "D" in chord_runs

    # Global cache should remain untouched (no song files written)
    songs_dir = cache_dir / "songs"
    assert not songs_dir.exists() or len(list(songs_dir.glob("*.json"))) == 0


def test_generate_from_songs_with_override_and_transposition(temp_workspace):
    from repertorio.generator import generate_from_songs
    from repertorio.parser import parse_text_to_lines

    output_docx = temp_workspace["output_docx"]
    cache_dir = temp_workspace["cache_dir"]

    custom_chord_sheet = (
        "G        C\n"
        "Acoustic version lyrics\n"
        "      D           G\n"
        "Closing line"
    )
    override_lines = parse_text_to_lines(custom_chord_sheet)

    songs = [
        {
            "artist": "Sample Artist",
            "title": "Sample Song",
            "dns": "sample-artist",
            "url": "sample-song",
            "key": "G",
            "semitones": 2,  # Transpose +2 semitones: G -> A, C -> D, D -> E
            "override": {
                "lines": override_lines,
                "is_modified": True,
            },
        }
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        stats = generate_from_songs(songs, output_docx, cache_dir=cache_dir)
        assert mock_urlopen.call_count == 0
        assert stats["total"] == 1
        assert stats["cached"] == 1

    doc = docx.Document(output_docx)
    all_text = "\n".join([p.text for p in doc.paragraphs])

    # Key metadata reflects active transposition and original reference
    assert "Tono: A (Original: G)" in all_text
    assert "Acoustic version lyrics" in all_text

    # Chords must be shifted by +2
    chord_runs = []
    for p in doc.paragraphs:
        for r in p.runs:
            if r.bold and r.font.color and r.font.color.rgb == RGBColor(230, 81, 0):
                chord_runs.append(r.text)

    assert "A" in chord_runs
    assert "D" in chord_runs
    assert "E" in chord_runs
    # Original untransposed chords should not be present
    assert "G" not in chord_runs
    assert "C" not in chord_runs


def test_parse_chord_color():
    # None returns default
    assert parse_chord_color(None) == DEFAULT_CHORD_COLOR

    # RGBColor instance returned as-is
    custom_rgb = RGBColor(12, 34, 56)
    assert parse_chord_color(custom_rgb) is custom_rgb

    # 6-digit hex string with #
    assert parse_chord_color("#000000") == RGBColor(0, 0, 0)
    assert parse_chord_color("#ffffff") == RGBColor(255, 255, 255)
    assert parse_chord_color("#E65100") == DEFAULT_CHORD_COLOR

    # 6-digit hex string without #
    assert parse_chord_color("000000") == RGBColor(0, 0, 0)
    assert parse_chord_color("e65100") == DEFAULT_CHORD_COLOR

    # 3-digit hex string with and without #
    assert parse_chord_color("#000") == RGBColor(0, 0, 0)
    assert parse_chord_color("#fff") == RGBColor(255, 255, 255)
    assert parse_chord_color("000") == RGBColor(0, 0, 0)
    assert parse_chord_color("f00") == RGBColor(255, 0, 0)

    # RGB tuple and list
    assert parse_chord_color((0, 0, 0)) == RGBColor(0, 0, 0)
    assert parse_chord_color((230, 81, 0)) == DEFAULT_CHORD_COLOR
    assert parse_chord_color([100, 150, 200]) == RGBColor(100, 150, 200)

    # Invalid values fallback gracefully to DEFAULT_CHORD_COLOR
    assert parse_chord_color("invalid") == DEFAULT_CHORD_COLOR
    assert parse_chord_color("#12345") == DEFAULT_CHORD_COLOR
    assert parse_chord_color("#gggggg") == DEFAULT_CHORD_COLOR
    assert parse_chord_color((1, 2)) == DEFAULT_CHORD_COLOR
    assert parse_chord_color((1, 2, 3, 4)) == DEFAULT_CHORD_COLOR
    assert parse_chord_color((-1, 0, 0)) == DEFAULT_CHORD_COLOR
    assert parse_chord_color((256, 0, 0)) == DEFAULT_CHORD_COLOR
    assert parse_chord_color(12345) == DEFAULT_CHORD_COLOR
    assert parse_chord_color(["invalid", "values", "here"]) == DEFAULT_CHORD_COLOR


def test_get_layout_preset():
    preset_1 = get_layout_preset(1)
    assert preset_1["columns"] == 1
    assert preset_1["font_size"] == Pt(10.5)
    assert preset_1["line_spacing"] == Pt(13.0)

    preset_2 = get_layout_preset(2)
    assert preset_2["columns"] == 2
    assert preset_2["font_size"] == Pt(8.5)
    assert preset_2["line_spacing"] == Pt(10.5)

    # String input parsing
    assert get_layout_preset("1") == preset_1
    assert get_layout_preset("2") == preset_2

    # Fallback to 2-column preset on invalid/unsupported input
    assert get_layout_preset() == preset_2
    assert get_layout_preset(3) == preset_2
    assert get_layout_preset(0) == preset_2
    assert get_layout_preset(-1) == preset_2
    assert get_layout_preset("invalid") == preset_2
    assert get_layout_preset(None) == preset_2


@pytest.fixture
def sample_song():
    from repertorio.parser import parse_text_to_lines

    sheet = (
        "[Intro] Am  F  C  G\n"
        "\n"
        "Am        F\n"
        "Sample song lyrics line\n"
        "      C           G\n"
        "Another lyric line"
    )
    return {
        "title": "Test Title",
        "artist": "Test Artist",
        "key": "Am",
        "capo": "1",
        "semitones": 0,
        "lines": parse_text_to_lines(sheet),
    }


def test_build_document_one_column_layout(tmp_path, sample_song):
    out_file = tmp_path / "1_col.docx"
    build_document([sample_song], out_file, columns=1)

    doc = docx.Document(out_file)
    section = doc.sections[0]
    cols = section._sectPr.xpath("./w:cols")
    assert len(cols) > 0
    assert cols[0].get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num") == "1"

    # Verify metadata font size
    meta_p = doc.paragraphs[1]  # Title is 0, meta is 1
    assert "Tono: Am | Capo: 1" in meta_p.text
    assert meta_p.runs[0].font.size == Pt(10.5)

    # Verify line spacing and font size on lyrics & chords
    lyric_paragraphs = [p for p in doc.paragraphs[2:] if p.text.strip()]
    assert len(lyric_paragraphs) > 0
    for p in lyric_paragraphs:
        assert p.paragraph_format.line_spacing == Pt(13.0)
        for r in p.runs:
            assert r.font.size == Pt(10.5)


def test_build_document_two_column_layout(tmp_path, sample_song):
    out_file = tmp_path / "2_col.docx"
    build_document([sample_song], out_file, columns=2)

    doc = docx.Document(out_file)
    section = doc.sections[0]
    cols = section._sectPr.xpath("./w:cols")
    assert len(cols) > 0
    assert cols[0].get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num") == "2"

    meta_p = doc.paragraphs[1]
    assert "Tono: Am | Capo: 1" in meta_p.text
    assert meta_p.runs[0].font.size == Pt(8.5)

    lyric_paragraphs = [p for p in doc.paragraphs[2:] if p.text.strip()]
    assert len(lyric_paragraphs) > 0
    for p in lyric_paragraphs:
        assert p.paragraph_format.line_spacing == Pt(10.5)
        for r in p.runs:
            assert r.font.size == Pt(8.5)


def test_chord_color_customization(tmp_path, sample_song):
    # 1. Custom hex #000000 (black)
    out_black = tmp_path / "black_chords.docx"
    build_document([sample_song], out_black, chord_color="#000000")
    doc_black = docx.Document(out_black)
    black_chord_runs = [
        r for p in doc_black.paragraphs for r in p.runs if r.bold and r.text in {"Am", "F", "C", "G"}
    ]
    assert len(black_chord_runs) > 0
    for r in black_chord_runs:
        assert r.font.color.rgb == RGBColor(0, 0, 0)

    # 2. RGB tuple (0, 128, 0)
    out_rgb = tmp_path / "rgb_chords.docx"
    build_document([sample_song], out_rgb, chord_color=(0, 128, 0))
    doc_rgb = docx.Document(out_rgb)
    rgb_chord_runs = [
        r for p in doc_rgb.paragraphs for r in p.runs if r.bold and r.text in {"Am", "F", "C", "G"}
    ]
    assert len(rgb_chord_runs) > 0
    for r in rgb_chord_runs:
        assert r.font.color.rgb == RGBColor(0, 128, 0)

    # 3. RGBColor object
    out_obj = tmp_path / "obj_chords.docx"
    build_document([sample_song], out_obj, chord_color=RGBColor(255, 0, 0))
    doc_obj = docx.Document(out_obj)
    red_chord_runs = [
        r for p in doc_obj.paragraphs for r in p.runs if r.bold and r.text in {"Am", "F", "C", "G"}
    ]
    assert len(red_chord_runs) > 0
    for r in red_chord_runs:
        assert r.font.color.rgb == RGBColor(255, 0, 0)

    # 4. Default when omitted or None -> #E65100
    out_default = tmp_path / "default_chords.docx"
    build_document([sample_song], out_default)
    doc_default = docx.Document(out_default)
    default_chord_runs = [
        r for p in doc_default.paragraphs for r in p.runs if r.bold and r.text in {"Am", "F", "C", "G"}
    ]
    assert len(default_chord_runs) > 0
    for r in default_chord_runs:
        assert r.font.color.rgb == RGBColor(230, 81, 0)


def test_transposition_and_override_with_1_column_and_custom_color(temp_workspace):
    from repertorio.generator import generate_from_songs
    from repertorio.parser import parse_text_to_lines

    output_docx = temp_workspace["output_docx"]
    cache_dir = temp_workspace["cache_dir"]

    custom_chord_sheet = (
        "C        F\n"
        "One column layout lyrics\n"
        "      G           C\n"
        "Second line here"
    )
    override_lines = parse_text_to_lines(custom_chord_sheet)

    songs = [
        {
            "artist": "Test Artist",
            "title": "Test Title",
            "dns": "test-artist",
            "url": "test-title",
            "key": "C",
            "semitones": 2,  # Transpose +2: C -> D, F -> G, G -> A
            "override": {
                "lines": override_lines,
                "is_modified": True,
            },
        }
    ]

    stats = generate_from_songs(
        songs,
        output_docx,
        cache_dir=cache_dir,
        columns=1,
        chord_color="#000000",
    )
    assert stats["total"] == 1
    assert stats["cached"] == 1

    doc = docx.Document(output_docx)
    section = doc.sections[0]
    cols = section._sectPr.xpath("./w:cols")
    assert cols[0].get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num") == "1"

    # Verify metadata
    meta_p = doc.paragraphs[1]
    assert "Tono: D (Original: C)" in meta_p.text
    assert meta_p.runs[0].font.size == Pt(10.5)

    # Verify custom lyrics and 13 pt line spacing
    lyric_paragraphs = [p for p in doc.paragraphs[2:] if p.text.strip()]
    for p in lyric_paragraphs:
        assert p.paragraph_format.line_spacing == Pt(13.0)

    # Verify chords are shifted and black with 10.5 pt font
    chord_runs = []
    for p in doc.paragraphs:
        for r in p.runs:
            if r.bold and r.font.color and r.font.color.rgb == RGBColor(0, 0, 0):
                assert r.font.size == Pt(10.5)
                chord_runs.append(r.text)

    assert "D" in chord_runs
    assert "G" in chord_runs
    assert "A" in chord_runs
    assert "C" not in chord_runs
    assert "F" not in chord_runs


def test_generate_repertoire_with_columns_and_chord_color(temp_workspace):
    songs_file = temp_workspace["songs_file"]
    output_docx = temp_workspace["output_docx"]
    cache_dir = temp_workspace["cache_dir"]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_solr_resp = MagicMock()
        mock_solr_resp.read.return_value = json.dumps(MOCK_SOLR_RESPONSE).encode("utf-8")
        mock_solr_resp.__enter__.return_value = mock_solr_resp

        mock_page_resp = MagicMock()
        mock_page_resp.read.return_value = MOCK_HTML_PAGE.encode("utf-8")
        mock_page_resp.__enter__.return_value = mock_page_resp

        mock_urlopen.side_effect = [mock_solr_resp, mock_page_resp]

        stats = generate_repertoire(
            songs_file,
            output_docx,
            cache_dir=cache_dir,
            columns=1,
            chord_color="#000000",
        )
        assert stats["downloaded"] == 1

    doc = docx.Document(output_docx)
    section = doc.sections[0]
    cols = section._sectPr.xpath("./w:cols")
    assert cols[0].get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num") == "1"

    chord_runs = []
    for p in doc.paragraphs:
        if p.text.strip() and not p.text.startswith("De Música Ligera"):
            assert p.paragraph_format.line_spacing == Pt(13.0)
        for r in p.runs:
            if r.bold and r.font.color and r.font.color.rgb == RGBColor(0, 0, 0):
                assert r.font.size == Pt(10.5)
                chord_runs.append(r.text)

    assert "Bm" in chord_runs
    assert "G" in chord_runs
    assert "D" in chord_runs
    assert "A" in chord_runs


def test_cli_columns_and_chord_color(monkeypatch, tmp_path):
    from repertorio.cli import main as cli_main

    input_file = tmp_path / "canciones.txt"
    input_file.write_text("de musica ligera\n", encoding="utf-8")
    output_docx = tmp_path / "repertorio.docx"

    called_args = {}

    def mock_generate(songs_file, output_path, cache_dir=".cache_cifras", columns=2, chord_color=None):
        called_args["songs_file"] = songs_file
        called_args["output_path"] = output_path
        called_args["cache_dir"] = cache_dir
        called_args["columns"] = columns
        called_args["chord_color"] = chord_color
        return {"total": 1, "downloaded": 1, "cached": 0, "failed": 0}

    monkeypatch.setattr("repertorio.cli.generate_repertoire", mock_generate)
    monkeypatch.setattr(
        "sys.argv",
        [
            "repertorio",
            "-i",
            str(input_file),
            "-o",
            str(output_docx),
            "--columns",
            "1",
            "--chord-color",
            "#000000",
        ],
    )

    cli_main()

    assert called_args["columns"] == 1
    assert called_args["chord_color"] == "#000000"


