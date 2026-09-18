from repertorio.cleaner import is_tab_line, filter_and_clean_lines


def test_is_tab_line():
    assert is_tab_line("E|-------------15----14---------|") is True
    assert is_tab_line("B|----15------------------------|") is True
    assert is_tab_line("G|-------14-12----14----14------|") is True
    assert is_tab_line("e|--3/5-3--|") is True
    assert is_tab_line("   A|--0-2-3--|  ") is True
    assert is_tab_line("|------------------------|") is True
    assert is_tab_line("------------------------|") is True

    # Non-tab lines
    assert is_tab_line("Ella durmio") is False
    assert is_tab_line("[Intro] Bm  G  D  A") is False
    assert is_tab_line("Bm        G  D") is False
    assert is_tab_line("") is False


def test_filter_and_clean_lines():
    raw_lines = [
        [{"text": "", "is_chord": False}],  # Leading empty line
        [{"text": "[Intro] ", "is_chord": False}, {"text": "Bm", "is_chord": True}],
        [{"text": "E|---0---2---|", "is_chord": False}],  # Tab
        [{"text": "B|---1---3---|", "is_chord": False}],  # Tab
        [{"text": "", "is_chord": False}],
        [{"text": "", "is_chord": False}],  # Multiple empty lines
        [{"text": "Ella durmio", "is_chord": False}],
        [{"text": "", "is_chord": False}],  # Trailing empty line
    ]

    cleaned = filter_and_clean_lines(raw_lines)

    # Tab lines removed, leading/trailing empty stripped, multiple empties collapsed
    assert len(cleaned) == 3
    assert cleaned[0][0]["text"] == "[Intro] "
    assert cleaned[1][0]["text"] == ""  # Single empty line
    assert cleaned[2][0]["text"] == "Ella durmio"
