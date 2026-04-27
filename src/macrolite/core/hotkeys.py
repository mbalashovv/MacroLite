from __future__ import annotations

from collections.abc import Callable

from macrolite.core.actions import normalize_key


class AppHotkeys:
    def __init__(
        self,
        *,
        on_record_toggle: Callable[[], None],
        on_play: Callable[[], None],
        on_key_down: Callable[[object], None] | None = None,
        on_key_up: Callable[[object], None] | None = None,
        record_key: str = "f8",
        play_key: str = "f12",
    ) -> None:
        self.on_record_toggle = on_record_toggle
        self.on_play = on_play
        self.on_key_down = on_key_down
        self.on_key_up = on_key_up
        self.record_key = record_key
        self.play_key = play_key
        self._listener = None

    def start(self) -> None:
        if self._listener is not None:
            return

        from pynput import keyboard

        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
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
        elif self.on_key_down is not None:
            self.on_key_down(key)
        return None

    def _on_release(self, key: object) -> bool | None:
        key_name = normalize_key(key)
        if key_name not in {self.record_key, self.play_key} and self.on_key_up is not None:
            self.on_key_up(key)
        return None
