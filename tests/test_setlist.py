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

    # Persistence verification
    assert cache_file.exists()
    s2 = Setlist(persistence_path=cache_file)
    assert len(s2.songs) == 2
    assert s2.songs[0]["title"] == "De Musica Ligera"

    # Export / Import
    export_file = tmp_path / "custom_export.json"
    s2.export_to_file(export_file)
    assert export_file.exists()

    s3 = Setlist(persistence_path=tmp_path / "empty.json")
    added = s3.import_from_file(export_file)
    assert added == 2
    assert len(s3.songs) == 2

    # Remove song
    removed = s.remove_song(0)
    assert removed["title"] == "De Musica Ligera"
    assert len(s.songs) == 1

    # Clear
    s.clear()
    assert len(s.songs) == 0
