import re
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, font, messagebox


@dataclass
class Line:
    start_word_index: int
    words: list[str]


class TeleprompterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Teleprompter")
        self.root.geometry("1180x760")
        self.root.minsize(920, 600)
        self.root.configure(bg="#101010")

        self.words: list[str] = []
        self.lines: list[Line] = []
        self.job_id: str | None = None
        self.scroll_offset = 0.0
        self.is_scrolling = False
        self.current_line_index = 0
        self.current_word_index = 0

        self.font_size_var = tk.IntVar(value=48)
        self.display_width_var = tk.IntVar(value=760)
        self.speed_var = tk.IntVar(value=220)
        self.visible_lines_var = tk.IntVar(value=5)

        self.display_font = font.Font(
            family="Helvetica",
            size=self.font_size_var.get(),
            weight="bold",
        )

        self._build_ui()
        self._refresh_display_style()
        self.root.after(50, self._render)

    def _build_ui(self) -> None:
        controls = tk.Frame(self.root, bg="#1b1b1b", padx=16, pady=14)
        controls.pack(side="top", fill="x")

        tk.Button(
            controls,
            text="Textdatei öffnen",
            command=self.load_text_file,
            padx=12,
            pady=8,
        ).grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="ns")

        self.file_label = tk.Label(
            controls,
            text="Keine Datei geladen",
            bg="#1b1b1b",
            fg="#dddddd",
            anchor="w",
        )
        self.file_label.grid(row=0, column=1, columnspan=8, sticky="ew", pady=(0, 8))

        tk.Label(controls, text="Schriftgröße", bg="#1b1b1b", fg="#f0f0f0").grid(
            row=1, column=1, sticky="w"
        )
        tk.Scale(
            controls,
            from_=24,
            to=110,
            orient="horizontal",
            variable=self.font_size_var,
            command=self._on_style_change,
            bg="#1b1b1b",
            fg="#f0f0f0",
            highlightthickness=0,
            troughcolor="#333333",
            length=150,
        ).grid(row=1, column=2, padx=(8, 12), sticky="w")

        tk.Label(controls, text="Breite", bg="#1b1b1b", fg="#f0f0f0").grid(
            row=1, column=3, sticky="w"
        )
        tk.Scale(
            controls,
            from_=350,
            to=1100,
            orient="horizontal",
            variable=self.display_width_var,
            command=self._on_style_change,
            bg="#1b1b1b",
            fg="#f0f0f0",
            highlightthickness=0,
            troughcolor="#333333",
            length=150,
        ).grid(row=1, column=4, padx=(8, 12), sticky="w")

        tk.Label(controls, text="Zeilen", bg="#1b1b1b", fg="#f0f0f0").grid(
            row=1, column=5, sticky="w"
        )
        tk.Scale(
            controls,
            from_=3,
            to=9,
            orient="horizontal",
            variable=self.visible_lines_var,
            command=self._on_style_change,
            bg="#1b1b1b",
            fg="#f0f0f0",
            highlightthickness=0,
            troughcolor="#333333",
            length=120,
        ).grid(row=1, column=6, padx=(8, 12), sticky="w")

        tk.Label(controls, text="Basis-WPM", bg="#1b1b1b", fg="#f0f0f0").grid(
            row=1, column=7, sticky="w"
        )
        tk.Scale(
            controls,
            from_=60,
            to=500,
            orient="horizontal",
            variable=self.speed_var,
            command=self._on_speed_change,
            bg="#1b1b1b",
            fg="#f0f0f0",
            highlightthickness=0,
            troughcolor="#333333",
            length=150,
        ).grid(row=1, column=8, padx=(8, 0), sticky="w")

        for column in range(1, 9):
            controls.grid_columnconfigure(column, weight=1)

        self.canvas = tk.Canvas(self.root, bg="#101010", highlightthickness=0, bd=0)
        self.canvas.pack(expand=True, fill="both")

        bottom_bar = tk.Frame(self.root, bg="#1b1b1b", padx=16, pady=14)
        bottom_bar.pack(side="bottom", fill="x")

        tk.Button(bottom_bar, text="Start", command=self.start, padx=18, pady=8).pack(
            side="left", padx=(0, 8)
        )
        tk.Button(bottom_bar, text="Pause", command=self.pause, padx=18, pady=8).pack(
            side="left", padx=8
        )
        tk.Button(
            bottom_bar, text="Zurücksetzen", command=self.reset, padx=18, pady=8
        ).pack(side="left", padx=8)

        self.status_label = tk.Label(
            bottom_bar,
            text="Bereit",
            bg="#1b1b1b",
            fg="#cfcfcf",
            anchor="e",
        )
        self.status_label.pack(side="right")

        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def load_text_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Textdatei auswählen",
            filetypes=[
                ("Textdateien", "*.txt"),
                ("Markdown", "*.md"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not file_path:
            return

        path = Path(file_path)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding="latin-1")
            except OSError as exc:
                messagebox.showerror("Fehler", f"Datei konnte nicht gelesen werden:\n{exc}")
                return
        except OSError as exc:
            messagebox.showerror("Fehler", f"Datei konnte nicht gelesen werden:\n{exc}")
            return

        self.pause()
        self.words = content.split()
        self.file_label.config(text=str(path))

        if not self.words:
            self.lines = []
            self.current_line_index = 0
            self.current_word_index = 0
            self._render("Die Datei ist leer")
            self.status_label.config(text="Keine Wörter gefunden")
            return

        self.current_line_index = 0
        self.current_word_index = 0
        self.scroll_offset = 0.0
        self.is_scrolling = False
        self._rebuild_lines(keep_progress=False)
        self.status_label.config(text=f"{len(self.words)} Wörter geladen")

    def start(self) -> None:
        if not self.lines:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Textdatei laden.")
            return
        if self.job_id is not None:
            return

        self.status_label.config(text="Läuft")
        if self.is_scrolling:
            self._animate_scroll_step()
        else:
            self._schedule_current_word()

    def pause(self) -> None:
        if self.job_id is not None:
            self.root.after_cancel(self.job_id)
            self.job_id = None
        self.status_label.config(text="Pausiert" if self.lines else "Bereit")

    def reset(self) -> None:
        self.pause()
        self.current_line_index = 0
        self.current_word_index = 0
        self.scroll_offset = 0.0
        self.is_scrolling = False
        self._render("Datei laden und Start drücken" if not self.lines else None)
        self.status_label.config(text="Zurückgesetzt" if self.lines else "Bereit")

    def _on_style_change(self, _value: str) -> None:
        was_running = self.job_id is not None
        self.pause()
        self._refresh_display_style()
        self._rebuild_lines(keep_progress=True)
        if was_running:
            self.start()

    def _on_speed_change(self, _value: str) -> None:
        was_running = self.job_id is not None
        self.pause()
        self._render()
        if was_running:
            self.start()

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        self._render()

    def _refresh_display_style(self) -> None:
        self.display_font.configure(size=self.font_size_var.get())

    def _rebuild_lines(self, keep_progress: bool) -> None:
        global_word_index = 0
        if keep_progress and self.lines:
            global_word_index = self.lines[self.current_line_index].start_word_index + self.current_word_index

        self.lines = self._wrap_words_into_lines(self.words)
        self.scroll_offset = 0.0
        self.is_scrolling = False

        if not self.lines:
            self.current_line_index = 0
            self.current_word_index = 0
            self._render("Datei laden und Start drücken")
            return

        self.current_line_index, self.current_word_index = self._locate_word(global_word_index)
        self._render()

    def _wrap_words_into_lines(self, words: list[str]) -> list[Line]:
        max_width = self.display_width_var.get()
        wrapped_lines: list[Line] = []
        index = 0

        while index < len(words):
            line_words: list[str] = []
            start_index = index

            while index < len(words):
                candidate = line_words + [words[index]]
                if line_words and self.display_font.measure(" ".join(candidate)) > max_width:
                    break
                line_words = candidate
                index += 1

            if not line_words:
                line_words = [words[index]]
                index += 1

            wrapped_lines.append(Line(start_word_index=start_index, words=line_words))

        return wrapped_lines

    def _locate_word(self, global_word_index: int) -> tuple[int, int]:
        if not self.lines:
            return 0, 0

        target = min(max(global_word_index, 0), len(self.words) - 1)
        for line_index, line in enumerate(self.lines):
            line_end = line.start_word_index + len(line.words)
            if target < line_end:
                return line_index, target - line.start_word_index

        last_index = len(self.lines) - 1
        return last_index, max(len(self.lines[last_index].words) - 1, 0)

    def _schedule_current_word(self) -> None:
        if self.current_line_index >= len(self.lines):
            self._finish()
            return

        self._render()
        duration_ms = self._word_duration_ms(self._current_word())
        self.job_id = self.root.after(duration_ms, self._advance_word)

    def _advance_word(self) -> None:
        self.job_id = None
        if self.current_line_index >= len(self.lines):
            self._finish()
            return

        line = self.lines[self.current_line_index]
        if self.current_word_index < len(line.words) - 1:
            self.current_word_index += 1
            self._schedule_current_word()
            return

        if self.current_line_index >= len(self.lines) - 1:
            self._finish()
            return

        self.current_word_index = len(line.words) - 1
        self._start_scroll()

    def _start_scroll(self) -> None:
        self.is_scrolling = True
        self.scroll_offset = 0.0
        self._animate_scroll_step()

    def _animate_scroll_step(self) -> None:
        self._render()
        step = max(2.0, self._line_height() / 18)
        self.scroll_offset -= step

        if abs(self.scroll_offset) >= self._line_height():
            self.current_line_index += 1
            self.current_word_index = 0
            self.scroll_offset = 0.0
            self.is_scrolling = False
            self.job_id = None
            self._schedule_current_word()
            return

        self.job_id = self.root.after(16, self._animate_scroll_step)

    def _finish(self) -> None:
        self.job_id = None
        self.is_scrolling = False
        if self.lines:
            self.current_word_index = len(self.lines[self.current_line_index].words) - 1
        self._render()
        self.status_label.config(text="Fertig")

    def _current_word(self) -> str:
        if not self.lines:
            return ""
        line = self.lines[self.current_line_index]
        safe_index = min(self.current_word_index, len(line.words) - 1)
        return line.words[safe_index]

    def _render(self, placeholder: str | None = None) -> None:
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        left, right = self._visible_bounds()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        line_height = self._line_height()

        self.canvas.create_rectangle(
            0, 0, canvas_width, canvas_height, fill="#101010", outline="#101010"
        )
        self.canvas.create_rectangle(
            left,
            center_y - line_height * 0.78,
            right,
            center_y + line_height * 0.78,
            fill="#181818",
            outline="#4a4a4a",
            width=2,
        )

        if placeholder is not None:
            self.canvas.create_text(
                center_x,
                center_y,
                text=placeholder,
                fill="#f2f2f2",
                font=self.display_font,
                anchor="center",
            )
            return

        if not self.lines:
            self.canvas.create_text(
                center_x,
                center_y,
                text="Datei laden und Start drücken",
                fill="#f2f2f2",
                font=self.display_font,
                anchor="center",
            )
            return

        focus_line = self._focused_visual_line()
        start_line = max(self.current_line_index - self._focus_slot(), 0)
        end_line = min(start_line + self.visible_lines_var.get(), len(self.lines))

        if end_line - start_line < self.visible_lines_var.get():
            start_line = max(end_line - self.visible_lines_var.get(), 0)

        for line_index in range(start_line, end_line):
            y_pos = center_y + (line_index - self.current_line_index) * line_height + self.scroll_offset
            if y_pos < -line_height or y_pos > canvas_height + line_height:
                continue

            if line_index == focus_line:
                word_index = self.current_word_index if not self.is_scrolling and line_index == self.current_line_index else None
                self._draw_focus_line(self.lines[line_index], center_x, y_pos, word_index)
            else:
                distance = abs(y_pos - center_y) / max(line_height, 1)
                shade = self._shade_for_distance(distance)
                self.canvas.create_text(
                    center_x,
                    y_pos,
                    text=" ".join(self.lines[line_index].words),
                    fill=shade,
                    font=self.display_font,
                    anchor="center",
                )

    def _draw_focus_line(
        self, line: Line, center_x: float, y_pos: float, highlighted_word_index: int | None
    ) -> None:
        words = line.words
        if not words:
            return

        total_width = self.display_font.measure(" ".join(words))
        x_pos = center_x - (total_width / 2)
        space_width = self.display_font.measure(" ")

        for index, word in enumerate(words):
            word_width = self.display_font.measure(word)
            if highlighted_word_index is None:
                color = "#f4f4f4"
            elif index < highlighted_word_index:
                color = "#ffffff"
            elif index == highlighted_word_index:
                color = self._highlight_color_for_word(word)
            else:
                color = "#d6d6d6"

            self.canvas.create_text(
                x_pos,
                y_pos,
                text=word,
                fill=color,
                font=self.display_font,
                anchor="w",
            )
            x_pos += word_width + space_width

    def _focused_visual_line(self) -> int:
        if not self.lines:
            return 0

        visible_count = self.visible_lines_var.get()
        best_line = self.current_line_index
        best_distance = float("inf")

        start_line = max(self.current_line_index - self._focus_slot(), 0)
        end_line = min(start_line + visible_count, len(self.lines))
        center_y = self.canvas.winfo_height() / 2
        line_height = self._line_height()

        for line_index in range(start_line, end_line):
            y_pos = center_y + (line_index - self.current_line_index) * line_height + self.scroll_offset
            distance = abs(y_pos - center_y)
            if distance < best_distance:
                best_distance = distance
                best_line = line_index

        return best_line

    def _focus_slot(self) -> int:
        return self.visible_lines_var.get() // 2

    def _visible_bounds(self) -> tuple[float, float]:
        canvas_width = self.canvas.winfo_width()
        visible_width = min(self.display_width_var.get(), canvas_width - 40)
        left = (canvas_width - visible_width) / 2
        return left, left + visible_width

    def _line_height(self) -> float:
        return self.font_size_var.get() * 1.55

    def _shade_for_distance(self, distance: float) -> str:
        if distance <= 1.2:
            return "#a8a8a8"
        if distance <= 2.2:
            return "#777777"
        return "#545454"

    def _highlight_color_for_word(self, word: str) -> str:
        duration = self._word_duration_ms(word)
        if duration < 220:
            return "#7be495"
        if duration < 360:
            return "#ffd166"
        return "#ff9f68"

    def _word_duration_ms(self, word: str) -> int:
        normalized = re.sub(r"[^\wäöüÄÖÜß]", "", word, flags=re.UNICODE)
        char_count = len(normalized) or 1
        base_word_ms = 60000 / max(self.speed_var.get(), 1)

        length_factor = 0.55 + min(char_count, 20) / 10
        punctuation_bonus = 0.0
        if any(mark in word for mark in [",", ";", ":"]):
            punctuation_bonus += 0.22
        if any(mark in word for mark in [".", "!", "?"]):
            punctuation_bonus += 0.45
        if "-" in word:
            punctuation_bonus += 0.12

        duration_ms = base_word_ms * (length_factor + punctuation_bonus)
        return max(120, int(duration_ms))


def main() -> None:
    root = tk.Tk()
    TeleprompterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
