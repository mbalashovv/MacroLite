from __future__ import annotations

from collections.abc import Callable

from macrolite.core.actions import normalize_key


class AppHotkeys:
    def __init__(
        self,
        *,
        on_record_toggle: Callable[[], None],
        on_play: Callable[[], None],
        record_key: str = "f8",
        play_key: str = "f12",
    ) -> None:
        self.on_record_toggle = on_record_toggle
        self.on_play = on_play
        self.record_key = record_key
        self.play_key = play_key
        self._listener = None

    def start(self) -> None:
        if self._listener is not None:
            return

        from pynput import keyboard

        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None

    def _on_press(self, key: object) -> bool | None:
        key_name = normalize_key(key)
        if key_name == self.record_key:
            self.on_record_toggle()
        elif key_name == self.play_key:
            self.on_play()
        return None
