from __future__ import annotations

import threading
import time
from collections.abc import Callable

from macrolite.core.actions import MacroAction

ProgressCallback = Callable[[str], None]

PYDIRECTINPUT_KEY_ALIASES = {
    "alt_l": "altleft",
    "alt_r": "altright",
    "caps_lock": "capslock",
    "cmd": "win",
    "cmd_l": "winleft",
    "cmd_r": "winright",
    "ctrl_l": "ctrlleft",
    "ctrl_r": "ctrlright",
    "page_down": "pagedown",
    "page_up": "pageup",
    "shift_l": "shiftleft",
    "shift_r": "shiftright",
}


class MacroPlayer:
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def play_async(
        self,
        actions: list[MacroAction],
        *,
        loop_count: int = 1,
        speed: float = 1.0,
        on_status: ProgressCallback | None = None,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        if self.is_playing:
            raise RuntimeError("Player is already running")
        if not actions:
            raise ValueError("No actions to play")
        if speed <= 0:
            raise ValueError("Playback speed must be greater than zero")

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(list(actions), loop_count, speed, on_status, on_finished),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(
        self,
        actions: list[MacroAction],
        loop_count: int,
        speed: float,
        on_status: ProgressCallback | None,
        on_finished: Callable[[], None] | None,
    ) -> None:
        try:
            import pyautogui
            import pydirectinput

            pyautogui.PAUSE = 0
            pydirectinput.PAUSE = 0

            iteration = 0
            while not self._stop_event.is_set() and (loop_count == 0 or iteration < loop_count):
                iteration += 1
                self._emit(on_status, f"Playing loop {iteration}" if loop_count else f"Playing loop {iteration} (infinite)")
                self._play_once(pyautogui, pydirectinput, actions, speed)
        except Exception as exc:
            self._emit(on_status, f"Playback error: {exc}")
        finally:
            if on_finished is not None:
                on_finished()

    def _play_once(
        self,
        pyautogui: object,
        pydirectinput: object,
        actions: list[MacroAction],
        speed: float,
    ) -> None:
        loop_started_at = time.perf_counter()
        for action in actions:
            if self._stop_event.is_set():
                return

            target_elapsed = action.time / speed
            elapsed = time.perf_counter() - loop_started_at
            wait_time = max(0.0, target_elapsed - elapsed)
            if self._sleep_interruptible(wait_time):
                return

            self._execute_action(pyautogui, pydirectinput, action)

    def _execute_action(
        self,
        pyautogui: object,
        pydirectinput: object,
        action: MacroAction,
    ) -> None:
        if action.type == "mouse_move" and action.x is not None and action.y is not None:
            pydirectinput.moveTo(action.x, action.y)
        elif action.type == "mouse_down" and action.x is not None and action.y is not None:
            pydirectinput.moveTo(action.x, action.y)
            pydirectinput.mouseDown(button=_to_pydirectinput_button(action.button))
        elif action.type == "mouse_up" and action.x is not None and action.y is not None:
            pydirectinput.moveTo(action.x, action.y)
            pydirectinput.mouseUp(button=_to_pydirectinput_button(action.button))
        elif action.type == "mouse_scroll":
            if action.x is not None and action.y is not None:
                pyautogui.moveTo(action.x, action.y)
            pyautogui.scroll(action.dy or 0)
        elif action.type == "key_down" and action.key:
            pydirectinput.keyDown(_to_pydirectinput_key(action.key))
        elif action.type == "key_up" and action.key:
            pydirectinput.keyUp(_to_pydirectinput_key(action.key))

    def _sleep_interruptible(self, seconds: float) -> bool:
        deadline = time.perf_counter() + seconds
        while time.perf_counter() < deadline:
            if self._stop_event.is_set():
                return True
            time.sleep(min(0.01, max(0.0, deadline - time.perf_counter())))
        return self._stop_event.is_set()

    def _emit(self, callback: ProgressCallback | None, message: str) -> None:
        if callback is not None:
            callback(message)


def _to_pydirectinput_key(key: str) -> str:
    return PYDIRECTINPUT_KEY_ALIASES.get(key, key.lower() if len(key) == 1 else key)


def _to_pydirectinput_button(button: str | None) -> str:
    if button in {"left", "right", "middle"}:
        return button
    return "left"
