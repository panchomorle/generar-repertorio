import pytest
from repertorio.parser import (
    is_chord_token,
    is_chord_line,
    parse_text_to_lines,
    format_lines_to_text,
)
from repertorio.transposer import transpose_lines


class TestChordTokenRecognition:
    def test_basic_triads(self):
        assert is_chord_token("C") is True
        assert is_chord_token("D") is True
        assert is_chord_token("E") is True
        assert is_chord_token("F") is True
        assert is_chord_token("G") is True
        assert is_chord_token("A") is True
        assert is_chord_token("B") is True

    def test_minors_and_accidentals(self):
        assert is_chord_token("Am") is True
        assert is_chord_token("Bm") is True
        assert is_chord_token("C#m") is True
        assert is_chord_token("F#m") is True
        assert is_chord_token("Bb") is True
        assert is_chord_token("Eb") is True
        assert is_chord_token("Abm") is True

    def test_extensions_and_tensions(self):
        assert is_chord_token("Gmaj7") is True
        assert is_chord_token("C7M") is True
        assert is_chord_token("Dsus4") is True
        assert is_chord_token("Csus2") is True
        assert is_chord_token("Am7(9)") is True
        assert is_chord_token("F#m7(b5)") is True
        assert is_chord_token("C7b9") is True
        assert is_chord_token("E7#9") is True
        assert is_chord_token("Cadd9") is True
        assert is_chord_token("A5") is True
        assert is_chord_token("Bdim") is True
        assert is_chord_token("Caug") is True
        assert is_chord_token("C+") is True
        assert is_chord_token("C°") is True

    def test_slash_chords(self):
        assert is_chord_token("D/F#") is True
        assert is_chord_token("C/E") is True
        assert is_chord_token("G/B") is True
        assert is_chord_token("Am/G") is True
        assert is_chord_token("Bb/D") is True
        assert is_chord_token("Bm7/A") is True

    def test_negative_words_not_chords(self):
        # Words starting with A-G in Spanish/English
        assert is_chord_token("Amor") is False
        assert is_chord_token("De") is False
        assert is_chord_token("El") is False
        assert is_chord_token("Ella") is False
        assert is_chord_token("Bien") is False
        assert is_chord_token("Cada") is False
        assert is_chord_token("Fui") is False
        assert is_chord_token("Gente") is False
        assert is_chord_token("Era") is False
        assert is_chord_token("Donde") is False
        assert is_chord_token("Al") is False
        assert is_chord_token("Asi") is False
        assert is_chord_token("Ayer") is False
        assert is_chord_token("And") is False
        assert is_chord_token("Before") is False
        assert is_chord_token("Can") is False
        assert is_chord_token("Every") is False
        assert is_chord_token("For") is False
        assert is_chord_token("Good") is False

    def test_empty_and_whitespace(self):
        assert is_chord_token("") is False
        assert is_chord_token("   ") is False


class TestChordLineRecognition:
    def test_pure_chord_lines(self):
        assert is_chord_line("Bm        G  D") is True
        assert is_chord_line("      A           Bm   G  D  A") is True
        assert is_chord_line("C  G/B  Am  Am/G  F  G7  C") is True
        assert is_chord_line("C#m7   F#m7(b5)   B7   Emaj7") is True

    def test_chord_line_with_section_prefix(self):
        assert is_chord_line("[Intro] Bm  G  D  A") is True
        assert is_chord_line("[Solo] Em  C  G  D") is True
        assert is_chord_line("Solo: G  Em  C  D") is True
        assert is_chord_line("Intro: Bm  G  D  A") is True

    def test_chord_line_with_measure_bars_and_repeats(self):
        assert is_chord_line("| Bm | G | D | A |") is True
        assert is_chord_line("| D/F# | G | A4 | (2x)") is True
        assert is_chord_line("Bm - G - D - A") is True
        assert is_chord_line("Bm  G  D  A (2x)") is True
        assert is_chord_line("Bm  G  D  A  pasaje") is True

    def test_single_chords_on_line(self):
        assert is_chord_line("Bm") is True
        assert is_chord_line("A") is True
        assert is_chord_line("   Gmaj7   ") is True

    def test_lyrics_lines_rejected(self):
        assert is_chord_line("Ella durmio al calor de las masas") is False
        assert is_chord_line("A veces te pienso cuando la tarde cae") is False
        assert is_chord_line("De musica ligera") is False
        assert is_chord_line("Ayer te vi pasar por la avenida") is False
        assert is_chord_line("A ti") is False
        assert is_chord_line("A Dios le pido") is False
        assert is_chord_line("Cada vez que te miro sonreír") is False
        assert is_chord_line("No le enviaremos cenizas de rosas") is False

    def test_section_headers_and_tabs_rejected(self):
        assert is_chord_line("[Intro]") is False
        assert is_chord_line("[Estribillo]") is False
        assert is_chord_line("[Verso 1]") is False
        assert is_chord_line("[Solo]") is False
        assert is_chord_line("[Coro]") is False
        assert is_chord_line("E|---0-2-3---|") is False
        assert is_chord_line("B|---1-0-1---|") is False

    def test_empty_lines_rejected(self):
        assert is_chord_line("") is False
        assert is_chord_line("    ") is False


class TestParseTextToLines:
    def test_parse_chords_above_lyrics(self):
        text = "Bm        G  D\nElla durmio"
        lines = parse_text_to_lines(text)
        assert len(lines) == 2

        # First line is chords
        chord_line = lines[0]
        assert chord_line[0] == {"text": "Bm", "is_chord": True}
        assert chord_line[1] == {"text": "        ", "is_chord": False}
        assert chord_line[2] == {"text": "G", "is_chord": True}
        assert chord_line[3] == {"text": "  ", "is_chord": False}
        assert chord_line[4] == {"text": "D", "is_chord": True}

        # Second line is lyrics
        lyric_line = lines[1]
        assert len(lyric_line) == 1
        assert lyric_line[0] == {"text": "Ella durmio", "is_chord": False}

    def test_preserve_indentation_and_offsets(self):
        text = "      A           Bm   G  D  A\nAl calor de las masas"
        lines = parse_text_to_lines(text)
        assert len(lines) == 2

        chord_line = lines[0]
        assert chord_line[0] == {"text": "      ", "is_chord": False}
        assert chord_line[1] == {"text": "A", "is_chord": True}
        assert chord_line[2] == {"text": "           ", "is_chord": False}
        assert chord_line[3] == {"text": "Bm", "is_chord": True}
        assert chord_line[4] == {"text": "   ", "is_chord": False}
        assert chord_line[5] == {"text": "G", "is_chord": True}
        assert chord_line[6] == {"text": "  ", "is_chord": False}
        assert chord_line[7] == {"text": "D", "is_chord": True}
        assert chord_line[8] == {"text": "  ", "is_chord": False}
        assert chord_line[9] == {"text": "A", "is_chord": True}

        # Reconstruction matches exactly
        assert "".join(t["text"] for t in chord_line) == "      A           Bm   G  D  A"

    def test_section_header_inline_with_chords(self):
        text = "[Intro] Bm  G  D  A"
        lines = parse_text_to_lines(text)
        assert len(lines) == 1
        tokens = lines[0]

        assert tokens[0] == {"text": "[Intro] ", "is_chord": False}
        assert tokens[1] == {"text": "Bm", "is_chord": True}
        assert tokens[3] == {"text": "G", "is_chord": True}
        assert tokens[5] == {"text": "D", "is_chord": True}
        assert tokens[7] == {"text": "A", "is_chord": True}

    def test_pure_section_header(self):
        text = "[Estribillo]\nNada mas queda"
        lines = parse_text_to_lines(text)
        assert len(lines) == 2
        assert lines[0] == [{"text": "[Estribillo]", "is_chord": False}]
        assert lines[1] == [{"text": "Nada mas queda", "is_chord": False}]

    def test_empty_and_whitespace_lines(self):
        text = "Bm  G\n\n\nElla durmio"
        lines = parse_text_to_lines(text)
        assert len(lines) == 4
        assert lines[1] == [{"text": "", "is_chord": False}]
        assert lines[2] == [{"text": "", "is_chord": False}]

    def test_empty_string(self):
        assert parse_text_to_lines("") == []

    def test_slash_chords_and_tensions_parsed(self):
        text = "D/F#   Gmaj7   A7sus4   Bm7(b5)"
        lines = parse_text_to_lines(text)
        chords = [t["text"] for t in lines[0] if t["is_chord"]]
        assert chords == ["D/F#", "Gmaj7", "A7sus4", "Bm7(b5)"]


class TestFormatLinesToText:
    def test_format_tokenized_lines(self):
        lines = [
            [
                {"text": "[Intro] ", "is_chord": False},
                {"text": "Bm", "is_chord": True},
                {"text": "  ", "is_chord": False},
                {"text": "G", "is_chord": True},
            ],
            [{"text": "", "is_chord": False}],
            [{"text": "Ella durmio", "is_chord": False}],
        ]
        text = format_lines_to_text(lines)
        expected = "[Intro] Bm  G\n\nElla durmio"
        assert text == expected

    def test_format_empty_lines(self):
        assert format_lines_to_text([]) == ""
        assert format_lines_to_text([[{"text": "", "is_chord": False}]]) == ""


class TestRoundtripAndTransposition:
    def test_roundtrip_consistency(self):
        original_sheet = (
            "[Intro] Bm  G  D  A\n"
            "\n"
            "Bm        G  D\n"
            "Ella durmio\n"
            "      A           Bm   G  D  A\n"
            "Al calor de las masas\n"
            "\n"
            "[Estribillo]\n"
            "D/F#   Gmaj7\n"
            "De musica ligera"
        )
        parsed = parse_text_to_lines(original_sheet)
        formatted = format_lines_to_text(parsed)
        assert formatted == original_sheet

    def test_parse_transpose_format_pipeline(self):
        sheet = (
            "[Intro] Bm  G  D  A\n"
            "\n"
            "Bm        G  D\n"
            "Ella durmio"
        )
        parsed = parse_text_to_lines(sheet)
        transposed = transpose_lines(parsed, 2)
        transposed_text = format_lines_to_text(transposed)

        expected = (
            "[Intro] C#m  A  E  B\n"
            "\n"
            "C#m        A  E\n"
            "Ella durmio"
        )
        assert transposed_text == expected

        # Transposing back by -2 restores the original chords
        restored = transpose_lines(parse_text_to_lines(transposed_text), -2)
        assert format_lines_to_text(restored) == sheet
