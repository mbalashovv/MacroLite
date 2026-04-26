from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ActionType = Literal[
    "mouse_move",
    "mouse_down",
    "mouse_up",
    "mouse_scroll",
    "key_down",
    "key_up",
]

MouseButton = Literal["left", "right", "middle", "unknown"]

VALID_ACTION_TYPES = {
    "mouse_move",
    "mouse_down",
    "mouse_up",
    "mouse_scroll",
    "key_down",
    "key_up",
}

SPECIAL_KEY_ALIASES = {
    "alt": "alt",
    "alt_l": "alt",
    "alt_r": "alt",
    "backspace": "backspace",
    "caps_lock": "capslock",
    "cmd": "win",
    "cmd_l": "winleft",
    "cmd_r": "winright",
    "ctrl": "ctrl",
    "ctrl_l": "ctrl",
    "ctrl_r": "ctrl",
    "delete": "delete",
    "down": "down",
    "end": "end",
    "enter": "enter",
    "esc": "esc",
    "f1": "f1",
    "f2": "f2",
    "f3": "f3",
    "f4": "f4",
    "f5": "f5",
    "f6": "f6",
    "f7": "f7",
    "f8": "f8",
    "f9": "f9",
    "f10": "f10",
    "f11": "f11",
    "f12": "f12",
    "home": "home",
    "insert": "insert",
    "left": "left",
    "menu": "apps",
    "page_down": "pagedown",
    "page_up": "pageup",
    "right": "right",
    "shift": "shift",
    "shift_l": "shift",
    "shift_r": "shift",
    "space": "space",
    "tab": "tab",
    "up": "up",
}


@dataclass(frozen=True)
class MacroAction:
    type: ActionType
    time: float
    x: int | None = None
    y: int | None = None
    button: MouseButton | None = None
    dx: int | None = None
    dy: int | None = None
    key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.type, "time": round(self.time, 4)}
        for field in ("x", "y", "button", "dx", "dy", "key"):
            value = getattr(self, field)
            if value is not None:
                data[field] = value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroAction":
        action_type = data.get("type")
        if action_type not in VALID_ACTION_TYPES:
            raise ValueError(f"Unsupported action type: {action_type!r}")
        try:
            action_time = float(data["time"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Action is missing a valid time value") from exc

        return cls(
            type=action_type,
            time=action_time,
            x=_optional_int(data.get("x")),
            y=_optional_int(data.get("y")),
            button=data.get("button"),
            dx=_optional_int(data.get("dx")),
            dy=_optional_int(data.get("dy")),
            key=data.get("key"),
        )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def normalize_button(button: object) -> MouseButton:
    name = getattr(button, "name", None)
    if name in {"left", "right", "middle"}:
        return name
    return "unknown"


def normalize_key(key: object) -> str:
    char = getattr(key, "char", None)
    if char:
        return str(char)

    name = getattr(key, "name", None)
    if name:
        return str(name)

    raw = str(key)
    if raw.startswith("Key."):
        return raw.removeprefix("Key.")
    return raw.strip("'")


def to_pyautogui_key(key: str) -> str:
    return SPECIAL_KEY_ALIASES.get(key, key)
