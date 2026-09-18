import os
import subprocess
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

from repertorio.search import search_songs
from repertorio.setlist import Setlist
from repertorio.generator import generate_from_songs


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class RepertoireApp(ctk.CTk):
    """Main desktop window for the Repertoire Generator."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Generador de Repertorio - CifraClub")
        self.geometry("900x720")
        self.minsize(800, 600)

        self.setlist = Setlist()
        self.search_results: List[Dict[str, Any]] = []
        self.is_generating = False
        self.last_generated_file: Optional[str] = None

        self._setup_ui()
        self.render_setlist()

    def _setup_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header & Search Frame
        search_frame = ctk.CTkFrame(self, corner_radius=10)
        search_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        header_lbl = ctk.CTkLabel(
            search_frame,
            text="Buscar canciones en CifraClub",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header_lbl.grid(row=0, column=0, columnspan=2, padx=15, pady=(12, 6), sticky="w")

        input_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Escribí el nombre de la canción o artista (ej: Spinetta, De música ligera)...",
            height=36,
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.search_entry.bind("<Return>", lambda event: self.start_search())

        self.search_btn = ctk.CTkButton(
            input_frame,
            text="Buscar",
            width=100,
            height=36,
            command=self.start_search,
        )
        self.search_btn.grid(row=0, column=1)

        # Container for Search Results dropdown/list
        self.results_frame = ctk.CTkScrollableFrame(search_frame, height=140, corner_radius=6)
        self.results_frame.grid_columnconfigure(0, weight=1)
        # Hidden initially
        self.results_frame.grid_remove()

        # 2. Setlist Header Frame
        setlist_header = ctk.CTkFrame(self, fg_color="transparent")
        setlist_header.grid(row=1, column=0, padx=20, pady=(5, 5), sticky="ew")
        setlist_header.grid_columnconfigure(0, weight=1)

        self.setlist_title_lbl = ctk.CTkLabel(
            setlist_header,
            text="Canciones en el Repertorio (0)",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.setlist_title_lbl.grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(setlist_header, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        import_btn = ctk.CTkButton(
            btn_box,
            text="Importar lista",
            width=110,
            height=28,
            fg_color="gray30",
            hover_color="gray40",
            command=self.import_setlist,
        )
        import_btn.pack(side="left", padx=5)

        export_btn = ctk.CTkButton(
            btn_box,
            text="Exportar lista",
            width=110,
            height=28,
            fg_color="gray30",
            hover_color="gray40",
            command=self.export_setlist,
        )
        export_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            btn_box,
            text="Vaciar",
            width=80,
            height=28,
            fg_color="firebrick3",
            hover_color="firebrick4",
            command=self.clear_setlist,
        )
        clear_btn.pack(side="left", padx=(5, 0))

        # 3. Setlist Scrollable Items Container
        self.setlist_container = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.setlist_container.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        self.setlist_container.grid_columnconfigure(1, weight=1)

        # 4. Output & Generation Frame
        bottom_frame = ctk.CTkFrame(self, corner_radius=10)
        bottom_frame.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="ew")
        bottom_frame.grid_columnconfigure(1, weight=1)

        # Output destination row
        out_lbl = ctk.CTkLabel(bottom_frame, text="Guardar como:", font=ctk.CTkFont(size=13))
        out_lbl.grid(row=0, column=0, padx=(15, 10), pady=(12, 5), sticky="w")

        self.output_entry = ctk.CTkEntry(bottom_frame, height=32)
        default_out = str(Path.cwd() / "repertorio.docx")
        self.output_entry.insert(0, default_out)
        self.output_entry.grid(row=0, column=1, padx=(0, 10), pady=(12, 5), sticky="ew")

        browse_btn = ctk.CTkButton(
            bottom_frame,
            text="Examinar...",
            width=90,
            height=32,
            fg_color="gray35",
            hover_color="gray45",
            command=self.browse_output_path,
        )
        browse_btn.grid(row=0, column=2, padx=(0, 15), pady=(12, 5))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(bottom_frame)
        self.progress_bar.grid(row=1, column=0, columnspan=3, padx=15, pady=(8, 4), sticky="ew")
        self.progress_bar.set(0)

        # Status & Generate button row
        action_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        action_row.grid(row=2, column=0, columnspan=3, padx=15, pady=(5, 12), sticky="ew")
        action_row.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            action_row,
            text="Listo para generar.",
            anchor="w",
            font=ctk.CTkFont(size=13),
        )
        self.status_lbl.grid(row=0, column=0, sticky="ew")

        # Action buttons shown after generation
        self.open_doc_btn = ctk.CTkButton(
            action_row,
            text="Abrir documento",
            width=130,
            height=36,
            fg_color="seagreen4",
            hover_color="seagreen",
            command=self.open_generated_document,
        )
        self.open_doc_btn.grid(row=0, column=1, padx=(0, 10))
        self.open_doc_btn.grid_remove()

        self.open_folder_btn = ctk.CTkButton(
            action_row,
            text="Abrir en explorador",
            width=150,
            height=36,
            fg_color="dodgerblue4",
            hover_color="dodgerblue3",
            command=self.open_in_file_explorer,
        )
        self.open_folder_btn.grid(row=0, column=2, padx=(0, 10))
        self.open_folder_btn.grid_remove()

        self.generate_btn = ctk.CTkButton(
            action_row,
            text="Generar Repertorio (.docx)",
            width=190,
            height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_generation,
        )
        self.generate_btn.grid(row=0, column=3)

    # --- Search Logic ---
    def start_search(self) -> None:
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_btn.configure(state="disabled", text="Buscando...")
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query: str) -> None:
        results = search_songs(query, limit=8)
        self.after(0, lambda: self._on_search_done(results))

    def _on_search_done(self, results: List[Dict[str, Any]]) -> None:
        self.search_btn.configure(state="normal", text="Buscar")
        self.search_results = results

        # Clear existing search widgets
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            lbl = ctk.CTkLabel(
                self.results_frame,
                text="No se encontraron canciones para esa búsqueda.",
                text_color="gray60",
            )
            lbl.pack(padx=10, pady=10)
        else:
            for item in results:
                row = ctk.CTkFrame(self.results_frame, fg_color="gray20", corner_radius=6)
                row.pack(fill="x", padx=4, pady=3)
                row.grid_columnconfigure(0, weight=1)

                text = f"{item.get('title')}  —  {item.get('artist')}"
                lbl = ctk.CTkLabel(row, text=text, anchor="w", font=ctk.CTkFont(size=13, weight="bold"))
                lbl.grid(row=0, column=0, padx=10, pady=6, sticky="w")

                add_btn = ctk.CTkButton(
                    row,
                    text="+ Agregar",
                    width=90,
                    height=26,
                    fg_color="forestgreen",
                    hover_color="darkgreen",
                    command=lambda s=item: self.add_to_setlist(s),
                )
                add_btn.grid(row=0, column=1, padx=10, pady=6)

        self.results_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 12), sticky="ew")

    def add_to_setlist(self, song: Dict[str, Any]) -> None:
        added = self.setlist.add_song(song)
        if not added:
            messagebox.showinfo("Información", f"'{song.get('title')}' ya está en el repertorio.")
            return
        self.render_setlist()

    # --- Setlist Management ---
    def render_setlist(self) -> None:
        for widget in self.setlist_container.winfo_children():
            widget.destroy()

        total = len(self.setlist.songs)
        self.setlist_title_lbl.configure(text=f"Canciones en el Repertorio ({total})")

        if total == 0:
            empty_lbl = ctk.CTkLabel(
                self.setlist_container,
                text="El repertorio está vacío.\nBuscá canciones arriba para agregarlas a la lista.",
                font=ctk.CTkFont(size=14),
                text_color="gray60",
            )
            empty_lbl.pack(expand=True, pady=40)
            return

        for idx, song in enumerate(self.setlist.songs):
            row = ctk.CTkFrame(self.setlist_container, fg_color="gray22", corner_radius=6)
            row.pack(fill="x", padx=5, pady=3)
            row.grid_columnconfigure(1, weight=1)

            # Number badge
            num_lbl = ctk.CTkLabel(
                row,
                text=f"{idx + 1}.",
                width=30,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="gray70",
            )
            num_lbl.grid(row=0, column=0, padx=(10, 5), pady=8)

            # Title & Artist
            title_text = f"{song.get('title')} — {song.get('artist')}"
            title_lbl = ctk.CTkLabel(
                row,
                text=title_text,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            title_lbl.grid(row=0, column=1, padx=5, pady=8, sticky="w")

            # Actions: Up, Down, Remove
            ctrls = ctk.CTkFrame(row, fg_color="transparent")
            ctrls.grid(row=0, column=2, padx=(5, 10), pady=4)

            up_btn = ctk.CTkButton(
                ctrls,
                text="▲",
                width=32,
                height=26,
                state="normal" if idx > 0 else "disabled",
                command=lambda i=idx: self.move_up(i),
            )
            up_btn.pack(side="left", padx=2)

            down_btn = ctk.CTkButton(
                ctrls,
                text="▼",
                width=32,
                height=26,
                state="normal" if idx < total - 1 else "disabled",
                command=lambda i=idx: self.move_down(i),
            )
            down_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(
                ctrls,
                text="✕",
                width=32,
                height=26,
                fg_color="firebrick3",
                hover_color="firebrick4",
                command=lambda i=idx: self.remove_song(i),
            )
            del_btn.pack(side="left", padx=(4, 0))

    def move_up(self, index: int) -> None:
        if self.setlist.move_up(index):
            self.render_setlist()

    def move_down(self, index: int) -> None:
        if self.setlist.move_down(index):
            self.render_setlist()

    def remove_song(self, index: int) -> None:
        self.setlist.remove_song(index)
        self.render_setlist()

    def clear_setlist(self) -> None:
        if not self.setlist.songs:
            return
        if messagebox.askyesno("Vaciar repertorio", "¿Seguro que querés quitar todas las canciones de la lista?"):
            self.setlist.clear()
            self.render_setlist()

    def export_setlist(self) -> None:
        if not self.setlist.songs:
            messagebox.showwarning("Atención", "No hay canciones en el repertorio para exportar.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="mi_repertorio.json",
        )
        if path:
            self.setlist.export_to_file(path)
            messagebox.showinfo("Exportado", f"Repertorio guardado con éxito en:\n{path}")

    def import_setlist(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
        )
        if path:
            count = self.setlist.import_from_file(path)
            self.render_setlist()
            messagebox.showinfo("Importado", f"Se agregaron {count} canciones al repertorio.")

    def browse_output_path(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialfile="repertorio.docx",
        )
        if path:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, path)

    # --- Generation Logic ---
    def start_generation(self) -> None:
        if self.is_generating:
            return

        if not self.setlist.songs:
            messagebox.showwarning("Atención", "Agregá al menos una canción al repertorio antes de generar.")
            return

        out_path = self.output_entry.get().strip()
        if not out_path:
            messagebox.showwarning("Atención", "Elegí una ruta de destino para el archivo Word.")
            return

        self.is_generating = True
        self.generate_btn.configure(state="disabled", text="Generando...")
        self.open_doc_btn.grid_remove()
        self.open_folder_btn.grid_remove()
        self.progress_bar.set(0)
        self.status_lbl.configure(text="Iniciando generación...")

        songs_copy = list(self.setlist.songs)
        threading.Thread(
            target=self._generation_worker,
            args=(songs_copy, out_path),
            daemon=True,
        ).start()

    def _generation_worker(self, songs: List[Dict[str, Any]], out_path: str) -> None:
        def update_progress(current: int, total: int, message: str) -> None:
            pct = current / max(total, 1)
            self.after(0, lambda: self._update_progress_ui(pct, message))

        try:
            stats = generate_from_songs(
                songs,
                output_docx=out_path,
                progress_callback=update_progress,
            )
            self.after(0, lambda: self._on_generation_success(stats, out_path))
        except Exception as exc:
            self.after(0, lambda: self._on_generation_error(str(exc)))

    def _update_progress_ui(self, pct: float, message: str) -> None:
        self.progress_bar.set(pct)
        self.status_lbl.configure(text=message)

    def _on_generation_success(self, stats: Dict[str, int], out_path: str) -> None:
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="Generar Repertorio (.docx)")
        self.progress_bar.set(1.0)
        self.last_generated_file = out_path

        summary = (
            f"¡Completado! {stats['downloaded']} descargadas | "
            f"{stats['cached']} en caché | {stats['failed']} fallidas."
        )
        self.status_lbl.configure(text=summary)

        self.open_doc_btn.grid()
        self.open_folder_btn.grid()

    def _on_generation_error(self, error_msg: str) -> None:
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="Generar Repertorio (.docx)")
        self.status_lbl.configure(text=f"Error durante la generación.")
        messagebox.showerror("Error al generar", f"Ocurrió un error inesperado:\n{error_msg}")

    # --- Open File & Reveal in Explorer ---
    def open_generated_document(self) -> None:
        if not self.last_generated_file or not os.path.exists(self.last_generated_file):
            messagebox.showwarning("Atención", "El archivo generado no existe o fue movido.")
            return
        try:
            os.startfile(self.last_generated_file)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{exc}")

    def open_in_file_explorer(self) -> None:
        if not self.last_generated_file:
            messagebox.showwarning("Atención", "No hay ningún archivo generado aún.")
            return

        abs_path = os.path.abspath(self.last_generated_file)
        try:
            if os.name == "nt":
                # Windows File Explorer reveal
                if os.path.exists(abs_path):
                    subprocess.run(["explorer", f"/select,{abs_path}"])
                else:
                    folder = os.path.dirname(abs_path)
                    os.startfile(folder)
            else:
                folder = os.path.dirname(abs_path)
                subprocess.run(["xdg-open", folder])
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo abrir el explorador:\n{exc}")


def run_app() -> None:
    app = RepertoireApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
