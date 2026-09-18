import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import docx
from docx.shared import RGBColor
import pytest

from repertorio.generator import generate_repertoire


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
