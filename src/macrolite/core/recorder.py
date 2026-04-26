from __future__ import annotations

import threading
import time
from collections.abc import Callable

from macrolite.core.actions import MacroAction, normalize_button, normalize_key
from macrolite.core.optimizer import compress_mouse_moves


class MacroRecorder:
    def __init__(
        self,
        *,
        mouse_move_sample_ms: int = 25,
        min_mouse_move_px: int = 3,
        start_delay_seconds: float = 0.0,
        on_stop_hotkey: Callable[[], None] | None = None,
    ) -> None:
        self.mouse_move_sample_ms = mouse_move_sample_ms
        self.min_mouse_move_px = min_mouse_move_px
        self.start_delay_seconds = start_delay_seconds
        self.on_stop_hotkey = on_stop_hotkey

        self._actions: list[MacroAction] = []
        self._lock = threading.Lock()
        self._recording = False
        self._start_time = 0.0
        self._capture_after = 0.0
        self._last_move_time = 0.0
        self._last_move_position: tuple[int, int] | None = None
        self._mouse_listener = None
        self._keyboard_listener = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        if self._recording:
            raise RuntimeError("Recorder is already running")

        from pynput import keyboard, mouse

        with self._lock:
            self._actions = []
            self._recording = True
            self._start_time = time.perf_counter()
            self._capture_after = self._start_time + self.start_delay_seconds
            self._last_move_time = 0.0
            self._last_move_position = None

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_down,
            on_release=self._on_key_up,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self) -> list[MacroAction]:
        if not self._recording:
            return self.actions()

        self._recording = False
        self._stop_listener(self._mouse_listener)
        self._stop_listener(self._keyboard_listener)
        self._mouse_listener = None
        self._keyboard_listener = None

        with self._lock:
            self._actions = compress_mouse_moves(self._actions)
            return list(self._actions)

    def actions(self) -> list[MacroAction]:
        with self._lock:
            return list(self._actions)

    def _stop_listener(self, listener: object | None) -> None:
        if listener is None:
            return
        stop = getattr(listener, "stop", None)
        if callable(stop):
            stop()

    def _can_capture(self) -> bool:
        return self._recording and time.perf_counter() >= self._capture_after

    def _timestamp(self) -> float:
        return max(0.0, time.perf_counter() - self._capture_after)

    def _append(self, action: MacroAction) -> None:
        with self._lock:
            if self._recording:
                self._actions.append(action)

    def _on_mouse_move(self, x: int, y: int) -> None:
        if not self._can_capture():
            return

        now = time.perf_counter()
        interval = self.mouse_move_sample_ms / 1000
        if now - self._last_move_time < interval:
            return

        position = (int(x), int(y))
        if self._last_move_position is not None:
            dx = abs(position[0] - self._last_move_position[0])
            dy = abs(position[1] - self._last_move_position[1])
            if dx < self.min_mouse_move_px and dy < self.min_mouse_move_px:
                return

        self._last_move_time = now
        self._last_move_position = position
        self._append(MacroAction(type="mouse_move", time=self._timestamp(), x=position[0], y=position[1]))

    def _on_mouse_click(self, x: int, y: int, button: object, pressed: bool) -> None:
        if not self._can_capture():
            return

        self._append(
            MacroAction(
                type="mouse_down" if pressed else "mouse_up",
                time=self._timestamp(),
                x=int(x),
                y=int(y),
                button=normalize_button(button),
            )
        )

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self._can_capture():
            return

        self._append(
            MacroAction(
                type="mouse_scroll",
                time=self._timestamp(),
                x=int(x),
                y=int(y),
                dx=int(dx),
                dy=int(dy),
            )
        )

    def _on_key_down(self, key: object) -> bool | None:
        key_name = normalize_key(key)
        if key_name == "f8":
            if self.on_stop_hotkey is not None:
                self.on_stop_hotkey()
            return False
        if key_name == "f12":
            return False

        if self._can_capture():
            self._append(MacroAction(type="key_down", time=self._timestamp(), key=key_name))
        return None

    def _on_key_up(self, key: object) -> bool | None:
        key_name = normalize_key(key)
        if key_name in {"f8", "f12"}:
            return False

        if self._can_capture():
            self._append(MacroAction(type="key_up", time=self._timestamp(), key=key_name))
        return None
