from __future__ import annotations

import sys
from pathlib import Path
from tkinter import BooleanVar, filedialog, messagebox

import customtkinter as ctk

from macrolite.core.exporter import export_macro_exe
from macrolite.core.hotkeys import AppHotkeys
from macrolite.core.player import MacroPlayer
from macrolite.core.recorder import MacroRecorder
from macrolite.core.storage import MacroFile, load_macro, save_macro


class MacroLiteWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("MacroLite")
        self._set_window_icon()
        self.geometry("940x700")
        self.minsize(860, 650)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.recorder = MacroRecorder(on_stop_hotkey=self._request_stop_from_hotkey)
        self.player = MacroPlayer()
        self.hotkeys = AppHotkeys(
            on_record_toggle=self._record_hotkey_threadsafe,
            on_play=self._play_hotkey_threadsafe,
        )
        self.actions = []
        self.current_file: Path | None = None

        self.status_var = ctk.StringVar(value="Ready")
        self.count_var = ctk.StringVar(value="0 actions")
        self.file_var = ctk.StringVar(value="No file loaded")
        self.loop_var = ctk.StringVar(value="1")
        self.speed_var = ctk.StringVar(value="1.0")
        self.continuous_var = BooleanVar(value=False)

        self._build_ui()
        self._start_hotkeys()
        self._refresh_controls()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_icon(self) -> None:
        icon_path = self._resource_path("icon.ico")
        if not icon_path.exists():
            return

        try:
            self.iconbitmap(str(icon_path))
        except Exception:
            # Missing/invalid icons should not prevent the app from starting.
            pass

    def _resource_path(self, relative_path: str) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS) / relative_path
        return Path(__file__).resolve().parents[3] / relative_path

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color="#101820")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="MacroLite", font=ctk.CTkFont(size=34, weight="bold")).grid(
            row=0, column=0, padx=28, pady=(22, 4), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="F8 starts/stops recording. F12 starts/stops playback.",
            text_color="#b8c7d9",
        ).grid(row=1, column=0, padx=28, pady=(0, 22), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=0, fg_color="#0b1117")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(content, corner_radius=22, fg_color="#14212d")
        left.grid(row=0, column=0, padx=(24, 12), pady=20, sticky="nsew")
        left.grid_columnconfigure((0, 1), weight=1)

        right = ctk.CTkFrame(content, corner_radius=22, fg_color="#16251d")
        right.grid(row=0, column=1, padx=(12, 24), pady=20, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Controls", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=22, pady=(20, 10), sticky="w"
        )

        self.record_button = ctk.CTkButton(left, text="Start Recording  (F8)", height=48, command=self.start_recording)
        self.record_button.grid(row=1, column=0, padx=(22, 10), pady=8, sticky="ew")

        self.stop_button = ctk.CTkButton(
            left,
            text="Stop",
            height=48,
            command=self.stop_all,
            fg_color="#a93636",
            hover_color="#7f2424",
        )
        self.stop_button.grid(row=1, column=1, padx=(10, 22), pady=8, sticky="ew")

        self.play_button = ctk.CTkButton(left, text="Play  (F12)", height=48, command=self.toggle_playback)
        self.play_button.grid(row=2, column=0, padx=(22, 10), pady=8, sticky="ew")

        self.save_button = ctk.CTkButton(left, text="Save Macro", height=48, command=self.save_macro)
        self.save_button.grid(row=2, column=1, padx=(10, 22), pady=8, sticky="ew")

        self.load_button = ctk.CTkButton(left, text="Load Macro", height=48, command=self.load_macro)
        self.load_button.grid(row=3, column=0, padx=(22, 10), pady=8, sticky="ew")

        self.export_button = ctk.CTkButton(left, text="Export EXE", height=48, command=self.export_exe)
        self.export_button.grid(row=3, column=1, padx=(10, 22), pady=8, sticky="ew")

        settings = ctk.CTkFrame(left, corner_radius=18, fg_color="#0f1922")
        settings.grid(row=4, column=0, columnspan=2, padx=22, pady=(18, 20), sticky="ew")
        settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings, text="Playback settings", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=18, pady=(18, 10), sticky="w"
        )
        ctk.CTkLabel(settings, text="Loop count").grid(row=1, column=0, padx=18, pady=8, sticky="w")
        self.loop_entry = ctk.CTkEntry(settings, textvariable=self.loop_var)
        self.loop_entry.grid(row=1, column=1, padx=18, pady=8, sticky="ew")

        ctk.CTkLabel(settings, text="Speed").grid(row=2, column=0, padx=18, pady=8, sticky="w")
        self.speed_entry = ctk.CTkEntry(settings, textvariable=self.speed_var)
        self.speed_entry.grid(row=2, column=1, padx=18, pady=8, sticky="ew")

        self.continuous_checkbox = ctk.CTkCheckBox(
            settings,
            text="Continuous playback until stopped",
            variable=self.continuous_var,
            command=self._refresh_controls,
        )
        self.continuous_checkbox.grid(row=3, column=0, columnspan=2, padx=18, pady=(10, 18), sticky="w")

        ctk.CTkLabel(right, text="Status", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=22, pady=(22, 12), sticky="w"
        )

        status_card = ctk.CTkFrame(right, corner_radius=18, fg_color="#0f1b14")
        status_card.grid(row=1, column=0, padx=22, pady=10, sticky="ew")
        status_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(status_card, textvariable=self.status_var, font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=18, pady=(18, 8), sticky="w"
        )
        ctk.CTkLabel(status_card, textvariable=self.count_var, text_color="#cde7d0").grid(
            row=1, column=0, padx=18, pady=(0, 18), sticky="w"
        )

        file_card = ctk.CTkFrame(right, corner_radius=18, fg_color="#0f1b14")
        file_card.grid(row=2, column=0, padx=22, pady=10, sticky="ew")
        file_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(file_card, text="Current file", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=18, pady=(18, 4), sticky="w"
        )
        ctk.CTkLabel(file_card, textvariable=self.file_var, wraplength=300, justify="left", text_color="#cde7d0").grid(
            row=1, column=0, padx=18, pady=(0, 18), sticky="w"
        )

        help_card = ctk.CTkFrame(right, corner_radius=18, fg_color="#0f1b14")
        help_card.grid(row=3, column=0, padx=22, pady=10, sticky="ew")
        ctk.CTkLabel(
            help_card,
            text="Mouse movement is recorded with sampled points. Macros use absolute screen coordinates, so keep target windows in the same position.",
            wraplength=300,
            justify="left",
            text_color="#e7d88c",
        ).grid(row=0, column=0, padx=18, pady=18, sticky="w")

    def _start_hotkeys(self) -> None:
        try:
            self.hotkeys.start()
        except Exception as exc:
            self.status_var.set(f"Hotkeys unavailable: {exc}")

    def start_recording(self) -> None:
        if self.player.is_playing:
            messagebox.showwarning("MacroLite", "Stop playback before recording.")
            return

        try:
            self.recorder.start()
        except Exception as exc:
            messagebox.showerror("MacroLite", f"Could not start recording:\n{exc}")
            self.status_var.set("Recording failed")
            return

        self.actions = []
        self.current_file = None
        self.file_var.set("Unsaved recording")
        self.count_var.set("0 actions")
        self.status_var.set("Recording")
        self._refresh_controls()

    def stop_all(self) -> None:
        if self.recorder.is_recording:
            self.actions = self.recorder.stop()
            self.count_var.set(f"{len(self.actions)} actions")
            self.status_var.set("Recording stopped")

        if self.player.is_playing:
            self.player.stop()
            self.status_var.set("Stopping playback")

        self._refresh_controls()

    def start_playback(self) -> None:
        if self.recorder.is_recording:
            messagebox.showwarning("MacroLite", "Stop recording before playback.")
            return
        if self.player.is_playing:
            return
        if not self.actions:
            messagebox.showwarning("MacroLite", "Record or load a macro first.")
            return

        try:
            loop_count, speed = self._playback_settings()
        except ValueError as exc:
            messagebox.showerror("MacroLite", str(exc))
            return

        try:
            self.player.play_async(
                self.actions,
                loop_count=loop_count,
                speed=speed,
                on_status=self._set_status_threadsafe,
                on_finished=self._playback_finished_threadsafe,
            )
        except Exception as exc:
            messagebox.showerror("MacroLite", f"Could not start playback:\n{exc}")
            return

        self.status_var.set("Playing")
        self._refresh_controls()

    def toggle_playback(self) -> None:
        if self.player.is_playing:
            self.player.stop()
            self.status_var.set("Stopping playback")
            self._refresh_controls()
            return
        self.start_playback()

    def save_macro(self) -> None:
        if not self.actions:
            messagebox.showwarning("MacroLite", "There is no macro to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save macro",
            defaultextension=".macro.json",
            filetypes=[("Macro files", "*.macro.json"), ("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            save_macro(path, self._macro_file())
        except Exception as exc:
            messagebox.showerror("MacroLite", f"Could not save macro:\n{exc}")
            return

        self.current_file = Path(path)
        self.file_var.set(str(self.current_file))
        self.status_var.set("Macro saved")

    def load_macro(self) -> None:
        if self.recorder.is_recording or self.player.is_playing:
            messagebox.showwarning("MacroLite", "Stop recording or playback before loading.")
            return

        path = filedialog.askopenfilename(
            title="Load macro",
            filetypes=[("Macro files", "*.macro.json"), ("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            macro = load_macro(path)
        except Exception as exc:
            messagebox.showerror("MacroLite", f"Could not load macro:\n{exc}")
            return

        self.actions = macro.actions
        self.current_file = Path(path)
        self.file_var.set(str(self.current_file))
        self.count_var.set(f"{len(self.actions)} actions")
        self.status_var.set("Macro loaded")
        self._refresh_controls()

    def export_exe(self) -> None:
        if not self.actions:
            messagebox.showwarning("MacroLite", "There is no macro to export.")
            return

        try:
            loop_count, speed = self._playback_settings()
        except ValueError as exc:
            messagebox.showerror("MacroLite", str(exc))
            return

        path = filedialog.asksaveasfilename(
            title="Export macro EXE",
            defaultextension=".exe",
            filetypes=[("Executable", "*.exe")],
        )
        if not path:
            return

        self.status_var.set("Exporting EXE")
        self._refresh_controls()
        self.update_idletasks()

        try:
            export_macro_exe(destination=path, macro=self._macro_file(), loop_count=loop_count, speed=speed)
        except Exception as exc:
            messagebox.showerror("MacroLite", f"Could not export EXE:\n{exc}")
            self.status_var.set("EXE export failed")
            self._refresh_controls()
            return

        self.status_var.set("EXE exported")
        messagebox.showinfo("MacroLite", "Macro EXE exported.")
        self._refresh_controls()

    def _playback_settings(self) -> tuple[int, float]:
        try:
            loop_count = 0 if self.continuous_var.get() else int(self.loop_var.get())
            speed = float(self.speed_var.get())
        except ValueError as exc:
            raise ValueError("Loop count must be an integer and speed must be a number.") from exc

        if loop_count < 0:
            raise ValueError("Loop count must be 0 or greater.")
        if speed <= 0:
            raise ValueError("Playback speed must be greater than 0.")
        return loop_count, speed

    def _macro_file(self) -> MacroFile:
        return MacroFile.create(actions=self.actions, screen=self._screen_metadata())

    def _screen_metadata(self) -> dict[str, int | float]:
        return {
            "width": self.winfo_screenwidth(),
            "height": self.winfo_screenheight(),
            "dpi_scale": self.winfo_fpixels("1i") / 96,
        }

    def _record_hotkey_threadsafe(self) -> None:
        self.after(0, self._handle_record_hotkey)

    def _play_hotkey_threadsafe(self) -> None:
        self.after(0, self.toggle_playback)

    def _handle_record_hotkey(self) -> None:
        if self.player.is_playing:
            return
        if self.recorder.is_recording:
            self.stop_all()
        else:
            self.start_recording()

    def _request_stop_from_hotkey(self) -> None:
        self.after(0, self.stop_all)

    def _set_status_threadsafe(self, message: str) -> None:
        self.after(0, self.status_var.set, message)

    def _playback_finished_threadsafe(self) -> None:
        self.after(0, self._playback_finished)

    def _playback_finished(self) -> None:
        if self.status_var.get().startswith("Stopping"):
            self.status_var.set("Playback stopped")
        elif self.status_var.get().startswith("Playback error"):
            pass
        else:
            self.status_var.set("Playback finished")
        self._refresh_controls()

    def _refresh_controls(self) -> None:
        recording = self.recorder.is_recording
        playing = self.player.is_playing
        has_actions = bool(self.actions)
        exporting = self.status_var.get() == "Exporting EXE"

        self.record_button.configure(
            text="Stop Recording  (F8)" if recording else "Start Recording  (F8)",
            state="disabled" if playing or exporting else "normal",
        )
        self.stop_button.configure(state="normal" if recording or playing else "disabled")
        self.play_button.configure(
            text="Stop Playback  (F12)" if playing else "Play  (F12)",
            state="normal" if ((has_actions and not recording and not exporting) or playing) else "disabled",
        )
        self.save_button.configure(state="normal" if has_actions and not recording and not playing and not exporting else "disabled")
        self.load_button.configure(state="disabled" if recording or playing or exporting else "normal")
        self.export_button.configure(state="normal" if has_actions and not recording and not playing and not exporting else "disabled")
        self.loop_entry.configure(state="disabled" if self.continuous_var.get() else "normal")

    def _on_close(self) -> None:
        self.hotkeys.stop()
        self.stop_all()
        self.destroy()
