import pytest
from repertorio.transposer import transpose_chord, transpose_key, transpose_lines


class TestTransposeKey:
    def test_transpose_key_basic_positive(self):
        assert transpose_key("C", 2) == "D"
        assert transpose_key("Bm", 2) == "C#m"
        assert transpose_key("Am", 3) == "Cm"

    def test_transpose_key_basic_negative(self):
        assert transpose_key("D", -2) == "C"
        assert transpose_key("C#m", -2) == "Bm"
        assert transpose_key("F", -1) == "E"

    def test_transpose_key_wrap_octave(self):
        assert transpose_key("B", 1) == "C"
        assert transpose_key("C", -1) == "B"
        assert transpose_key("G#m", 12) == "G#m"
        assert transpose_key("G#m", -12) == "G#m"

    def test_transpose_key_flats_and_sharps(self):
        assert transpose_key("Bb", 2) == "C"
        assert transpose_key("Eb", 1) == "E"
        assert transpose_key("F#", 1) == "G"

    def test_transpose_empty_or_none(self):
        assert transpose_key("", 2) == ""
        assert transpose_key(None, 2) is None


class TestTransposeChord:
    def test_simple_triads(self):
        assert transpose_chord("C", 2) == "D"
        assert transpose_chord("G", -2) == "F"
        assert transpose_chord("Am", 2) == "Bm"
        assert transpose_chord("Em", 1) == "Fm"

    def test_accidentals(self):
        assert transpose_chord("F#", 1) == "G"
        assert transpose_chord("Bb", 2) == "C"
        assert transpose_chord("Eb", -1) == "D"
        assert transpose_chord("C#m", -2) == "Bm"

    def test_extensions_and_qualities(self):
        assert transpose_chord("Gmaj7", 2) == "Amaj7"
        assert transpose_chord("C7", 2) == "D7"
        assert transpose_chord("Dsus4", 2) == "Esus4"
        assert transpose_chord("Am7(9)", 2) == "Bm7(9)"
        assert transpose_chord("F#m7(b5)", 1) == "Gm7(b5)"
        assert transpose_chord("Bdim", 1) == "Cdim"

    def test_slash_chords(self):
        assert transpose_chord("D/F#", 2) == "E/G#"
        assert transpose_chord("C/E", -1) == "B/D#"
        assert transpose_chord("Am/G", 2) == "Bm/A"
        assert transpose_chord("G/B", 1) == "Ab/C" or transpose_chord("G/B", 1) == "G#/C"

    def test_non_chord_strings(self):
        assert transpose_chord("", 2) == ""
        assert transpose_chord("   ", 2) == "   "
        assert transpose_chord("[Intro]", 2) == "[Intro]"


class TestTransposeLines:
    def test_transpose_tokenized_lines(self):
        lines = [
            [
                {"text": "[Intro] ", "is_chord": False},
                {"text": "Bm", "is_chord": True},
                {"text": "  ", "is_chord": False},
                {"text": "G", "is_chord": True},
            ],
            [
                {"text": "Ella durmió al calor de las masas", "is_chord": False}
            ]
        ]
        transposed = transpose_lines(lines, 2)

        # Chord line transposed
        assert transposed[0][0]["text"] == "[Intro] "
        assert transposed[0][0]["is_chord"] is False
        assert transposed[0][1]["text"] == "C#m"
        assert transposed[0][1]["is_chord"] is True
        assert transposed[0][2]["text"] == "  "
        assert transposed[0][3]["text"] == "A"
        assert transposed[0][3]["is_chord"] is True

        # Lyrics line unchanged
        assert transposed[1][0]["text"] == "Ella durmió al calor de las masas"
        assert transposed[1][0]["is_chord"] is False

    def test_transpose_zero_semitones_returns_identical(self):
        lines = [
            [{"text": "Bm", "is_chord": True}]
        ]
        transposed = transpose_lines(lines, 0)
        assert transposed[0][0]["text"] == "Bm"
