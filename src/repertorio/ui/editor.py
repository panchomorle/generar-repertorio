import queue
import threading
from typing import Optional, Callable

import customtkinter as ctk
from tkinter import messagebox

from repertorio.setlist import Setlist
from repertorio.cache import CacheManager
from repertorio.scraper import fetch_and_parse_song
from repertorio.parser import parse_text_to_lines, format_lines_to_text
from repertorio.transposer import transpose_key, transpose_lines


class SongEditModal(ctk.CTkToplevel):
    """Modal dialog for editing song chords and lyrics with live transposition."""

    def __init__(
        self,
        parent: Optional[ctk.CTk] = None,
        setlist: Optional[Setlist] = None,
        song_index: int = 0,
        cache: Optional[CacheManager] = None,
        on_save: Optional[Callable[[], None]] = None,
        on_restore: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)

        if setlist is None:
            raise ValueError("setlist must be provided to SongEditModal")

        self.setlist = setlist
        self.song_index = song_index
        self.cache = cache or CacheManager()
        self.on_save_callback = on_save
        self.on_restore_callback = on_restore

        self.song = self.setlist.songs[song_index]
        self.title_str = self.song.get("title", "Canción")
        self.artist_str = self.song.get("artist", "Artista")
        self.dns = self.song.get("dns", "")
        self.url = self.song.get("url", "")
        self.base_key = self.song.get("key")
        self.current_semitones = int(self.song.get("semitones", 0))
        self._fetch_thread: Optional[threading.Thread] = None

        self._setup_window(parent)
        self._setup_ui()
        self._load_content()

    def _setup_window(self, parent: Optional[ctk.CTk]) -> None:
        self.title(f"Editar canción: {self.title_str} — {self.artist_str}")
        self.geometry("820x680")
        self.minsize(640, 500)

        if parent:
            self.transient(parent)

        try:
            self.grab_set()
        except Exception:
            pass

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", lambda event: self.on_close())

    def _setup_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="w")

        title_lbl = ctk.CTkLabel(
            info_frame,
            text=f"{self.title_str} — {self.artist_str}",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            info_frame,
            text="Editor de acordes y letra (monoespaciado)",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            anchor="w",
        )
        sub_lbl.pack(anchor="w")

        # Transposition controls on the right
        trans_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        trans_frame.grid(row=0, column=1, sticky="e")

        self.key_lbl = ctk.CTkLabel(
            trans_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=140,
            anchor="e",
        )
        self.key_lbl.pack(side="left", padx=(0, 8))

        self.minus_btn = ctk.CTkButton(
            trans_frame,
            text="-",
            width=32,
            height=28,
            fg_color="gray30",
            hover_color="gray40",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.on_transpose_minus,
        )
        self.minus_btn.pack(side="left", padx=2)

        self.plus_btn = ctk.CTkButton(
            trans_frame,
            text="+",
            width=32,
            height=28,
            fg_color="gray30",
            hover_color="gray40",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.on_transpose_plus,
        )
        self.plus_btn.pack(side="left", padx=(2, 0))

        self._update_key_display()

        # 2. Text Editor Frame
        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none",
            corner_radius=8,
        )
        self.textbox.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")

        # 3. Footer Frame
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        has_override = self.setlist.has_song_override(self.song_index)
        self.restore_btn = ctk.CTkButton(
            footer,
            text="Restaurar original",
            width=140,
            height=34,
            fg_color="firebrick3" if has_override else "gray30",
            hover_color="firebrick4" if has_override else "gray30",
            state="normal" if has_override else "disabled",
            command=self.on_restore,
        )
        self.restore_btn.grid(row=0, column=0, sticky="w")

        actions_box = ctk.CTkFrame(footer, fg_color="transparent")
        actions_box.grid(row=0, column=1, sticky="e")

        self.close_btn = ctk.CTkButton(
            actions_box,
            text="Cerrar",
            width=100,
            height=34,
            fg_color="gray30",
            hover_color="gray40",
            command=self.on_close,
        )
        self.close_btn.pack(side="left", padx=(0, 10))

        self.save_btn = ctk.CTkButton(
            actions_box,
            text="Guardar cambios",
            width=140,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#E65100",
            hover_color="#BF360C",
            command=self.on_save,
        )
        self.save_btn.pack(side="left")

    def _update_key_display(self) -> None:
        if self.base_key:
            if self.current_semitones != 0:
                transposed_key = transpose_key(self.base_key, self.current_semitones)
                sign = f"+{self.current_semitones}" if self.current_semitones > 0 else str(self.current_semitones)
                text = f"Tono: {transposed_key} ({sign})"
                color = "#FFA726"
            else:
                text = f"Tono: {self.base_key}"
                color = "gray90"
        elif self.current_semitones != 0:
            sign = f"+{self.current_semitones}" if self.current_semitones > 0 else str(self.current_semitones)
            text = f"Tono: ({sign})"
            color = "#FFA726"
        else:
            text = "Tono: ..."
            color = "gray60"

        self.key_lbl.configure(text=text, text_color=color)

    def _load_content(self) -> None:
        lines = self.setlist.get_song_lines(self.song_index, cache=self.cache)
        if lines is not None:
            # If base_key is not set in song, attempt to read it from cache
            if not self.base_key and self.dns and self.url:
                slug = f"{self.dns}_{self.url}"
                cached = self.cache.get_by_slug(slug)
                if cached and cached.get("key"):
                    self.base_key = cached["key"]
                    self.setlist.set_song_key(self.song_index, self.base_key)
                    self._update_key_display()

            self._populate_textbox(lines)
            return

        # Not found in override or cache -> Fetch in background without freezing UI
        if self.dns and self.url:
            self.textbox.insert("1.0", "Descargando acordes desde CifraClub...")
            self.textbox.configure(state="disabled")
            self.save_btn.configure(state="disabled")
            self.plus_btn.configure(state="disabled")
            self.minus_btn.configure(state="disabled")

            self._fetch_queue = queue.Queue()
            self._fetch_thread = threading.Thread(target=self._fetch_worker, daemon=True)
            self._fetch_thread.start()
            self.after(50, self._check_fetch_queue)
        else:
            self._fetch_thread = None
            self.textbox.insert("1.0", "No se encontraron acordes disponibles para esta canción.")

    def _populate_textbox(self, lines: list) -> None:
        if self.current_semitones != 0:
            display_lines = transpose_lines(lines, self.current_semitones)
        else:
            display_lines = lines

        text = format_lines_to_text(display_lines)
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)
        self._update_key_display()

    def _fetch_worker(self) -> None:
        try:
            fetched = fetch_and_parse_song(
                self.dns,
                self.url,
                artist=self.artist_str,
                title=self.title_str,
            )
            if fetched and "lines" in fetched:
                slug = f"{self.dns}_{self.url}"
                self.cache.save(slug, fetched)
                self._fetch_queue.put(("success", fetched))
            else:
                self._fetch_queue.put(("error", "No se pudo obtener el contenido."))
        except Exception as exc:
            self._fetch_queue.put(("error", str(exc)))

    def _check_fetch_queue(self) -> None:
        if not self.winfo_exists():
            return
        try:
            status, payload = self._fetch_queue.get_nowait()
            if status == "success":
                self._on_fetch_success(payload)
            else:
                self._on_fetch_error(payload)
        except queue.Empty:
            if self._fetch_thread and self._fetch_thread.is_alive():
                self.after(50, self._check_fetch_queue)

    def _on_fetch_success(self, fetched: dict) -> None:
        if not self.winfo_exists():
            return
        if not self.base_key and fetched.get("key"):
            self.base_key = fetched["key"]
            self.setlist.set_song_key(self.song_index, self.base_key)

        self.save_btn.configure(state="normal")
        self.plus_btn.configure(state="normal")
        self.minus_btn.configure(state="normal")
        self._populate_textbox(fetched.get("lines", []))

    def _on_fetch_error(self, err: str) -> None:
        if not self.winfo_exists():
            return
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", f"Error al cargar la canción desde CifraClub:\n{err}")
        self.textbox.configure(state="disabled")

    def on_transpose_minus(self) -> None:
        self.on_transpose_delta(-1)

    def on_transpose_plus(self) -> None:
        self.on_transpose_delta(1)

    def on_transpose_delta(self, delta: int) -> None:
        self.current_semitones += delta
        self._update_key_display()

        current_text = self.textbox.get("1.0", "end-1c")
        if current_text.strip():
            yview = self.textbox.yview()
            lines = parse_text_to_lines(current_text)
            transposed = transpose_lines(lines, delta)
            new_text = format_lines_to_text(transposed)

            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", new_text)
            if yview:
                try:
                    self.textbox.yview_moveto(yview[0])
                except Exception:
                    pass

    def on_save(self) -> None:
        text = self.textbox.get("1.0", "end-1c")
        lines = parse_text_to_lines(text)

        # Normalize relative to base key (offset 0)
        if self.current_semitones != 0:
            normalized_lines = transpose_lines(lines, -self.current_semitones)
        else:
            normalized_lines = lines

        self.setlist.set_song_override(self.song_index, normalized_lines)
        self.setlist.songs[self.song_index]["semitones"] = self.current_semitones
        self.setlist.save_autosave()

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()

    def on_restore(self) -> None:
        if not self.setlist.has_song_override(self.song_index):
            return

        confirmed = messagebox.askyesno(
            "Restaurar original",
            "¿Deseás descartar los cambios y restaurar la versión original de CifraClub?",
            parent=self,
        )
        if confirmed:
            self.setlist.clear_song_override(self.song_index)
            if self.on_restore_callback:
                self.on_restore_callback()
            self.destroy()

    def on_close(self) -> None:
        self.destroy()
