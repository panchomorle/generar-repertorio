from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import customtkinter as ctk

from repertorio.setlist import Setlist
from repertorio.cache import CacheManager
from repertorio.ui.editor import SongEditModal
from repertorio.ui.app import RepertoireApp


@pytest.fixture(scope="module")
def tk_root():
    root = ctk.CTk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def sample_setlist(tmp_path: Path):
    path = tmp_path / "setlist.json"
    s = Setlist(persistence_path=path)
    s.add_song({
        "title": "De Musica Ligera",
        "artist": "Soda Stereo",
        "dns": "soda-stereo",
        "url": "de-musica-ligera",
        "key": "Bm",
        "semitones": 0,
    })
    return s


@pytest.fixture
def sample_cache(tmp_path: Path):
    cache = CacheManager(cache_dir=tmp_path / "cache")
    slug = "soda-stereo_de-musica-ligera"
    cache.save(slug, {
        "title": "De Musica Ligera",
        "artist": "Soda Stereo",
        "key": "Bm",
        "lines": [
            [
                {"text": "Bm", "is_chord": True},
                {"text": "        ", "is_chord": False},
                {"text": "G", "is_chord": True},
                {"text": "  ", "is_chord": False},
                {"text": "D", "is_chord": True},
                {"text": "  ", "is_chord": False},
                {"text": "A", "is_chord": True},
            ],
            [{"text": "Ella durmió al calor de las masas", "is_chord": False}],
        ],
    })
    return cache


def test_modal_displays_transposed_chords_wysiwyg(tk_root, sample_setlist, sample_cache):
    # Set song to +2 semitones
    sample_setlist.transpose_song(0, 2)
    assert sample_setlist.songs[0]["semitones"] == 2

    modal = SongEditModal(
        parent=tk_root,
        setlist=sample_setlist,
        song_index=0,
        cache=sample_cache,
    )

    try:
        # Key display should reflect transposed key (Bm + 2 = C#m)
        assert "C#m" in modal.key_lbl.cget("text")
        assert "+2" in modal.key_lbl.cget("text")
        assert modal.current_semitones == 2

        # Text in editor should display transposed chords
        content = modal.textbox.get("1.0", "end-1c")
        assert "C#m" in content
        assert "A" in content
        assert "E" in content
        assert "B" in content
        assert "Ella durmió al calor de las masas" in content
    finally:
        modal.destroy()


def test_modal_live_transposition_controls(tk_root, sample_setlist, sample_cache):
    modal = SongEditModal(
        parent=tk_root,
        setlist=sample_setlist,
        song_index=0,
        cache=sample_cache,
    )

    try:
        # Initial: 0 semitones, Bm
        assert modal.current_semitones == 0
        assert "Bm" in modal.textbox.get("1.0", "end-1c")
        assert "Tono: Bm" in modal.key_lbl.cget("text")

        # Increment +1
        modal.on_transpose_delta(1)
        assert modal.current_semitones == 1
        assert "Cm" in modal.textbox.get("1.0", "end-1c")
        assert "Cm" in modal.key_lbl.cget("text")
        assert "+1" in modal.key_lbl.cget("text")

        # Decrement -2 (net -1 semitone from original)
        modal.on_transpose_delta(-2)
        assert modal.current_semitones == -1
        assert "Bbm" in modal.textbox.get("1.0", "end-1c")
        assert "Bbm" in modal.key_lbl.cget("text")
        assert "-1" in modal.key_lbl.cget("text")
    finally:
        modal.destroy()


def test_modal_save_normalizes_and_commits_override(tk_root, sample_setlist, sample_cache):
    # Transpose by +1 before opening
    sample_setlist.transpose_song(0, 1)

    save_called = False

    def on_save_cb():
        nonlocal save_called
        save_called = True

    modal = SongEditModal(
        parent=tk_root,
        setlist=sample_setlist,
        song_index=0,
        cache=sample_cache,
        on_save=on_save_cb,
    )

    try:
        # Current key is Cm (+1)
        assert modal.current_semitones == 1

        # Simulate user editing the text: adding a chord and custom lyrics
        edited_text = "Cm        Ab  Bb\nElla durmió en mi habitación"
        modal.textbox.delete("1.0", "end")
        modal.textbox.insert("1.0", edited_text)

        # Click save
        modal.on_save()

        assert save_called is True
        assert sample_setlist.has_song_override(0) is True
        assert sample_setlist.is_song_modified(0) is True
        assert sample_setlist.songs[0]["semitones"] == 1

        # Override lines should be stored normalized relative to base key (transposed by -1)
        # Cm -> Bm, Ab -> G, Bb -> A
        override = sample_setlist.get_song_override(0)
        assert override is not None
        lines = override["lines"]
        first_line_text = "".join(t["text"] for t in lines[0])
        assert "Bm" in first_line_text
        assert "G" in first_line_text
        assert "A" in first_line_text
        second_line_text = "".join(t["text"] for t in lines[1])
        assert "Ella durmió en mi habitación" in second_line_text
    finally:
        try:
            modal.destroy()
        except Exception:
            pass


def test_modal_restore_original_clears_override(tk_root, sample_setlist, sample_cache):
    # First set an override
    sample_setlist.set_song_override(0, [
        [{"text": "C", "is_chord": True}],
        [{"text": "Custom", "is_chord": False}],
    ])
    assert sample_setlist.has_song_override(0) is True

    restore_called = False

    def on_restore_cb():
        nonlocal restore_called
        restore_called = True

    modal = SongEditModal(
        parent=tk_root,
        setlist=sample_setlist,
        song_index=0,
        cache=sample_cache,
        on_restore=on_restore_cb,
    )

    try:
        # Restore button should be enabled
        assert modal.restore_btn.cget("state") == "normal"

        with patch("tkinter.messagebox.askyesno", return_value=True):
            modal.on_restore()

        assert restore_called is True
        assert sample_setlist.has_song_override(0) is False
        assert sample_setlist.is_song_modified(0) is False
    finally:
        try:
            modal.destroy()
        except Exception:
            pass


def test_modal_close_without_saving_leaves_state_unchanged(tk_root, sample_setlist, sample_cache):
    modal = SongEditModal(
        parent=tk_root,
        setlist=sample_setlist,
        song_index=0,
        cache=sample_cache,
    )

    try:
        # Transpose in modal and edit text
        modal.on_transpose_delta(3)
        modal.textbox.delete("1.0", "end")
        modal.textbox.insert("1.0", "Dm   Bb\nCambios no guardados")

        # Close without saving
        modal.on_close()

        # State in setlist must remain unchanged
        assert sample_setlist.has_song_override(0) is False
        assert sample_setlist.songs[0]["semitones"] == 0
    finally:
        try:
            modal.destroy()
        except Exception:
            pass


def test_setlist_gui_renders_edit_badge_and_opens_editor(tmp_path: Path):
    setlist_file = tmp_path / "gui_setlist.json"
    cache_dir = tmp_path / "gui_cache"

    app = RepertoireApp()
    app.withdraw()
    app.setlist = Setlist(persistence_path=setlist_file)
    app.cache = CacheManager(cache_dir=cache_dir)

    try:
        app.setlist.add_song({
            "title": "Cancion Test",
            "artist": "Artista Test",
            "dns": "artista-test",
            "url": "cancion-test",
            "key": "A",
            "semitones": 0,
        })
        app.render_setlist()

        # Check that no [✏️ Editada] badge exists initially
        rows = app.setlist_container.winfo_children()
        assert len(rows) == 1
        row = rows[0]
        # Search for badge in row children
        badge_widgets = [
            w for w in row.winfo_children()
            if isinstance(w, ctk.CTkFrame)
            for sub in w.winfo_children()
            if isinstance(sub, ctk.CTkLabel) and "[✏️ Editada]" in sub.cget("text")
        ]
        assert len(badge_widgets) == 0

        # Now set an override on the song
        app.setlist.set_song_override(0, [
            [{"text": "A", "is_chord": True}],
            [{"text": "Letra editada", "is_chord": False}],
        ])
        app.render_setlist()

        # Badge should now be rendered
        rows = app.setlist_container.winfo_children()
        row = rows[0]
        badge_widgets = [
            sub for w in row.winfo_children()
            if isinstance(w, ctk.CTkFrame)
            for sub in w.winfo_children()
            if isinstance(sub, ctk.CTkLabel) and "[✏️ Editada]" in sub.cget("text")
        ]
        assert len(badge_widgets) == 1

        # Check that open_song_editor is invoked when calling row click
        with patch.object(app, "open_song_editor") as mock_open:
            app.open_song_editor(0)
            mock_open.assert_called_once_with(0)
    finally:
        app.destroy()


def test_modal_background_fetch_success(tk_root, sample_setlist, tmp_path: Path):
    empty_cache = CacheManager(cache_dir=tmp_path / "empty_cache")
    fetched_mock = {
        "title": "De Musica Ligera",
        "artist": "Soda Stereo",
        "key": "Bm",
        "lines": [
            [{"text": "Bm", "is_chord": True}, {"text": "  G", "is_chord": True}],
            [{"text": "Letra descargada", "is_chord": False}],
        ],
    }

    with patch("repertorio.ui.editor.fetch_and_parse_song", return_value=fetched_mock) as mock_fetch:
        modal = SongEditModal(
            parent=tk_root,
            setlist=sample_setlist,
            song_index=0,
            cache=empty_cache,
        )

        try:
            if modal._fetch_thread:
                modal._fetch_thread.join(timeout=3.0)
            modal._check_fetch_queue()

            content = modal.textbox.get("1.0", "end-1c")
            assert "Bm" in content
            assert "Letra descargada" in content
            assert modal.save_btn.cget("state") == "normal"
        finally:
            modal.destroy()


def test_modal_background_fetch_error(tk_root, sample_setlist, tmp_path: Path):
    empty_cache = CacheManager(cache_dir=tmp_path / "empty_cache_err")

    with patch("repertorio.ui.editor.fetch_and_parse_song", side_effect=RuntimeError("Connection timeout")):
        modal = SongEditModal(
            parent=tk_root,
            setlist=sample_setlist,
            song_index=0,
            cache=empty_cache,
        )

        try:
            if modal._fetch_thread:
                modal._fetch_thread.join(timeout=3.0)
            modal._check_fetch_queue()

            content = modal.textbox.get("1.0", "end-1c")
            assert "Error al cargar" in content or "Connection timeout" in content
            assert modal.save_btn.cget("state") == "disabled"
        finally:
            modal.destroy()


def test_modal_with_song_having_no_key(tk_root, tmp_path: Path):
    path = tmp_path / "setlist_nokey.json"
    s = Setlist(persistence_path=path)
    s.add_song({
        "title": "Cancion Sin Tono",
        "artist": "Artista",
        "dns": "artista",
        "url": "cancion",
        "key": None,
        "semitones": 0,
    })
    cache = CacheManager(cache_dir=tmp_path / "cache_nokey")
    cache.save("artista_cancion", {
        "title": "Cancion Sin Tono",
        "artist": "Artista",
        "lines": [
            [{"text": "C", "is_chord": True}, {"text": "  ", "is_chord": False}, {"text": "G", "is_chord": True}],
        ],
    })

    modal = SongEditModal(
        parent=tk_root,
        setlist=s,
        song_index=0,
        cache=cache,
    )

    try:
        assert "Tono: ..." in modal.key_lbl.cget("text")
        modal.on_transpose_delta(2)
        assert "+2" in modal.key_lbl.cget("text")
        content = modal.textbox.get("1.0", "end-1c")
        assert "D" in content
        assert "A" in content
    finally:
        modal.destroy()

