import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import customtkinter as ctk

from repertorio.settings import SettingsManager
from repertorio.setlist import Setlist
from repertorio.cache import CacheManager
from repertorio.ui.app import RepertoireApp


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("ui_controls")
    settings_file = tmp_path / "settings.json"
    settings = SettingsManager(persistence_path=settings_file)
    application = None
    for attempt in range(3):
        try:
            application = RepertoireApp(settings=settings)
            application.withdraw()
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.5)
    yield application
    try:
        if application:
            application.destroy()
    except Exception:
        pass


def test_ui_format_controls_rendered_with_defaults(app):
    # Check segmented button initialized to default (2 Columnas)
    assert hasattr(app, "layout_segmented_btn")
    assert app.layout_segmented_btn.get() == "2 Columnas"

    # Check hint label
    assert hasattr(app, "layout_hint_lbl")
    hint_text = app.layout_hint_lbl.cget("text")
    assert "1 columna se adapta mejor a pantallas" in hint_text
    assert "2 columnas es mejor para imprimir" in hint_text

    # Check chord color swatch button
    assert hasattr(app, "color_swatch_btn")
    assert app.color_swatch_btn.cget("fg_color").upper() == "#E65100"


def test_layout_toggle_updates_settings_and_persists(app):
    # Toggle to 1 Column
    app._on_layout_changed("1 Columna")
    assert app.settings.columns == 1

    # Check persisted file on disk
    reloaded = SettingsManager(persistence_path=app.settings.persistence_path)
    assert reloaded.columns == 1

    # Toggle back to 2 Columns
    app._on_layout_changed("2 Columnas")
    assert app.settings.columns == 2

    reloaded_2 = SettingsManager(persistence_path=app.settings.persistence_path)
    assert reloaded_2.columns == 2


def test_chord_color_picker_updates_swatch_and_persists(app):
    # 1. Successful selection
    with patch("repertorio.ui.app.colorchooser.askcolor", return_value=((0, 0, 0), "#000000")):
        app.pick_chord_color()

    assert app.settings.chord_color == "#000000"
    assert app.color_swatch_btn.cget("fg_color").upper() == "#000000"

    # Check persisted file
    reloaded = SettingsManager(persistence_path=app.settings.persistence_path)
    assert reloaded.chord_color == "#000000"

    # 2. Cancelled dialog
    with patch("repertorio.ui.app.colorchooser.askcolor", return_value=(None, None)):
        app.pick_chord_color()

    # Should remain unchanged
    assert app.settings.chord_color == "#000000"
    assert app.color_swatch_btn.cget("fg_color").upper() == "#000000"


def test_ui_format_controls_set_layout_and_color_methods(app):
    app.set_layout(1)
    assert app.settings.columns == 1
    assert app.layout_segmented_btn.get() == "1 Columna"

    app.update_chord_color("#FF5500")
    assert app.settings.chord_color == "#FF5500"
    assert app.color_swatch_btn.cget("fg_color").upper() == "#FF5500"

    # Restore defaults
    app.set_layout(2)
    app.update_chord_color("#E65100")


def test_generation_passes_active_layout_and_color(app, tmp_path: Path):
    setlist_file = tmp_path / "setlist.json"
    cache_dir = tmp_path / "cache"

    app.settings.update(columns=1, chord_color="#336699")
    app.setlist = Setlist(persistence_path=setlist_file)
    app.cache = CacheManager(cache_dir=cache_dir)

    app.setlist.add_song({
        "title": "Cancion Test",
        "artist": "Artista Test",
        "dns": "artista-test",
        "url": "cancion-test",
        "key": "G",
        "semitones": 0,
    })

    out_docx = str(tmp_path / "out.docx")
    app.output_entry.delete(0, "end")
    app.output_entry.insert(0, out_docx)

    with patch("repertorio.ui.app.generate_from_songs") as mock_gen:
        mock_gen.return_value = {"total": 1, "downloaded": 0, "cached": 1, "failed": 0}

        # Call _generation_worker directly to avoid async timing in test
        app._generation_worker(
            list(app.setlist.songs),
            out_docx,
            columns=app.settings.columns,
            chord_color=app.settings.chord_color,
        )

        mock_gen.assert_called_once()
        _, kwargs = mock_gen.call_args
        assert kwargs["columns"] == 1
        assert kwargs["chord_color"] == "#336699"


def test_start_generation_threads_with_active_settings(app, tmp_path: Path):
    app.settings.update(columns=1, chord_color="#112233")
    app.setlist.add_song({
        "title": "Test",
        "artist": "Test",
        "dns": "test",
        "url": "test",
    })
    out_docx = str(tmp_path / "out.docx")
    app.output_entry.delete(0, "end")
    app.output_entry.insert(0, out_docx)

    with patch("threading.Thread") as mock_thread_cls:
        mock_thread_inst = MagicMock()
        mock_thread_cls.return_value = mock_thread_inst

        app.start_generation()

        mock_thread_cls.assert_called_once()
        _, kwargs = mock_thread_cls.call_args
        target = kwargs["target"]
        args = kwargs["args"]

        assert target == app._generation_worker
        # args: (songs_copy, out_path, columns, chord_color)
        assert args[1] == out_docx
        assert args[2] == 1
        assert args[3] == "#112233"
        mock_thread_inst.start.assert_called_once()

