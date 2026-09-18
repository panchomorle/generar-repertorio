from pathlib import Path
from repertorio.setlist import Setlist


def test_setlist_operations(tmp_path: Path):
    cache_file = tmp_path / "test_setlist.json"
    s = Setlist(persistence_path=cache_file)

    assert len(s.songs) == 0

    # Add song
    song1 = {"title": "De Musica Ligera", "artist": "Soda Stereo", "dns": "soda-stereo", "url": "de-musica-ligera"}
    song2 = {"title": "The Scientist", "artist": "Coldplay", "dns": "coldplay", "url": "the-scientist"}

    assert s.add_song(song1) is True
    assert len(s.songs) == 1

    # Duplicate should not be added
    assert s.add_song(song1) is False
    assert len(s.songs) == 1

    # Add second song
    assert s.add_song(song2) is True
    assert len(s.songs) == 2

    # Move up/down
    assert s.move_down(0) is True
    assert s.songs[0]["title"] == "The Scientist"
    assert s.songs[1]["title"] == "De Musica Ligera"

    assert s.move_up(1) is True
    assert s.songs[0]["title"] == "De Musica Ligera"

    # Transposition and key
    assert s.songs[0]["key"] is None
    assert s.songs[0]["semitones"] == 0
    assert s.set_song_key(0, "Bm") is True
    assert s.songs[0]["key"] == "Bm"
    assert s.transpose_song(0, 2) == 2
    assert s.songs[0]["semitones"] == 2
    assert s.transpose_song(0, -1) == 1
    assert s.songs[0]["semitones"] == 1

    # Persistence verification
    assert cache_file.exists()
    s2 = Setlist(persistence_path=cache_file)
    assert len(s2.songs) == 2
    assert s2.songs[0]["title"] == "De Musica Ligera"
    assert s2.songs[0]["key"] == "Bm"
    assert s2.songs[0]["semitones"] == 1

    # Export / Import
    export_file = tmp_path / "custom_export.json"
    s2.export_to_file(export_file)
    assert export_file.exists()

    s3 = Setlist(persistence_path=tmp_path / "empty.json")
    added = s3.import_from_file(export_file)
    assert added == 2
    assert len(s3.songs) == 2
    assert s3.songs[0]["key"] == "Bm"
    assert s3.songs[0]["semitones"] == 1

    # Remove song
    removed = s.remove_song(0)
    assert removed["title"] == "De Musica Ligera"
    assert len(s.songs) == 1

    # Clear
    s.clear()
    assert len(s.songs) == 0


def test_song_override_crud_and_modification_flag(tmp_path: Path):
    cache_file = tmp_path / "setlist_override.json"
    s = Setlist(persistence_path=cache_file)
    song = {
        "title": "De Musica Ligera",
        "artist": "Soda Stereo",
        "dns": "soda-stereo",
        "url": "de-musica-ligera",
        "key": "Bm",
    }
    s.add_song(song)

    assert s.has_song_override(0) is False
    assert s.is_song_modified(0) is False
    assert s.get_song_override(0) is None

    custom_lines = [
        [{"text": "Bm", "is_chord": True}, {"text": "  ", "is_chord": False}, {"text": "G", "is_chord": True}],
        [{"text": "Ella durmio", "is_chord": False}],
    ]
    # Set override
    assert s.set_song_override(0, custom_lines) is True
    assert s.has_song_override(0) is True
    assert s.is_song_modified(0) is True

    override = s.get_song_override(0)
    assert override is not None
    assert override["is_modified"] is True
    assert override["lines"] == custom_lines

    # Clear override
    assert s.clear_song_override(0) is True
    assert s.has_song_override(0) is False
    assert s.is_song_modified(0) is False
    assert s.get_song_override(0) is None

    # Setting override using plain text string (via parse_text_to_lines)
    text_sheet = "Bm  G\nElla durmio"
    assert s.set_song_override(0, text_sheet) is True
    assert s.has_song_override(0) is True
    override_from_text = s.get_song_override(0)
    assert len(override_from_text["lines"]) == 2
    assert override_from_text["lines"][0][0]["text"] == "Bm"
    assert override_from_text["lines"][0][0]["is_chord"] is True

    # Clearing again returns True
    assert s.clear_song_override(0) is True
    # Clearing when already cleared returns False
    assert s.clear_song_override(0) is False


def test_song_override_persistence_and_reordering(tmp_path: Path):
    cache_file = tmp_path / "setlist_reorder.json"
    s = Setlist(persistence_path=cache_file)
    song1 = {"title": "Song 1", "artist": "Artist 1", "dns": "a1", "url": "s1"}
    song2 = {"title": "Song 2", "artist": "Artist 2", "dns": "a2", "url": "s2"}
    s.add_song(song1)
    s.add_song(song2)

    lines_override = [[{"text": "C", "is_chord": True}]]
    assert s.set_song_override(0, lines_override) is True

    # Move down
    assert s.move_down(0) is True
    assert s.songs[0]["title"] == "Song 2"
    assert s.has_song_override(0) is False
    assert s.songs[1]["title"] == "Song 1"
    assert s.has_song_override(1) is True
    assert s.get_song_override(1)["lines"] == lines_override

    # Add a third song
    song3 = {"title": "Song 3", "artist": "Artist 3", "dns": "a3", "url": "s3"}
    s.add_song(song3)
    assert len(s.songs) == 3
    assert s.has_song_override(1) is True

    # Reload from persistence
    s_reloaded = Setlist(persistence_path=cache_file)
    assert len(s_reloaded.songs) == 3
    assert s_reloaded.songs[1]["title"] == "Song 1"
    assert s_reloaded.has_song_override(1) is True
    assert s_reloaded.get_song_override(1)["lines"] == lines_override


def test_song_override_export_import(tmp_path: Path):
    cache_file = tmp_path / "setlist_source.json"
    export_file = tmp_path / "setlist_exported.json"
    s1 = Setlist(persistence_path=cache_file)
    song = {"title": "Song 1", "artist": "Artist 1", "dns": "a1", "url": "s1"}
    s1.add_song(song)
    lines_override = [[{"text": "Am", "is_chord": True}]]
    s1.set_song_override(0, lines_override)

    s1.export_to_file(export_file)

    s2 = Setlist(persistence_path=tmp_path / "setlist_dest.json")
    added = s2.import_from_file(export_file)
    assert added == 1
    assert s2.has_song_override(0) is True
    assert s2.get_song_override(0)["lines"] == lines_override


def test_get_song_lines_priority(tmp_path: Path):
    from unittest.mock import MagicMock
    cache_file = tmp_path / "setlist_lines.json"
    s = Setlist(persistence_path=cache_file)
    song = {"title": "Song 1", "artist": "Artist 1", "dns": "a1", "url": "s1"}
    s.add_song(song)

    # Mock cache
    mock_cache = MagicMock()
    cached_lines = [[{"text": "Cached line", "is_chord": False}]]
    mock_cache.get_by_slug.return_value = {"lines": cached_lines}

    # When no override, returns cached lines
    lines = s.get_song_lines(0, cache=mock_cache)
    assert lines == cached_lines

    # When override is set, returns override lines prioritizing over cache
    override_lines = [[{"text": "Override chord", "is_chord": True}]]
    s.set_song_override(0, override_lines)
    lines_after = s.get_song_lines(0, cache=mock_cache)
    assert lines_after == override_lines

