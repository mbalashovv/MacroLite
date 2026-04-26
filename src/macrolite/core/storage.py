from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from macrolite.core.actions import MacroAction

APP_NAME = "MacroLite"
MACRO_VERSION = 1


@dataclass(frozen=True)
class MacroFile:
    actions: list[MacroAction]
    created_at: str
    screen: dict[str, Any]
    settings: dict[str, Any]

    @classmethod
    def create(
        cls,
        actions: list[MacroAction],
        screen: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> "MacroFile":
        return cls(
            actions=actions,
            created_at=datetime.now(timezone.utc).isoformat(),
            screen=screen or {},
            settings=settings or {"mouse_move_sample_ms": 25, "playback_speed": 1.0},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": MACRO_VERSION,
            "app": APP_NAME,
            "created_at": self.created_at,
            "screen": self.screen,
            "settings": self.settings,
            "actions": [action.to_dict() for action in self.actions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroFile":
        if data.get("version") != MACRO_VERSION:
            raise ValueError(f"Unsupported macro file version: {data.get('version')!r}")
        raw_actions = data.get("actions")
        if not isinstance(raw_actions, list):
            raise ValueError("Macro file must contain an actions list")

        return cls(
            actions=[MacroAction.from_dict(item) for item in raw_actions],
            created_at=str(data.get("created_at", "")),
            screen=dict(data.get("screen", {})),
            settings=dict(data.get("settings", {})),
        )


def save_macro(path: str | Path, macro: MacroFile) -> None:
    destination = Path(path)
    destination.write_text(json.dumps(macro.to_dict(), indent=2), encoding="utf-8")


def load_macro(path: str | Path) -> MacroFile:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Macro file is not valid JSON") from exc

    if not isinstance(data, dict):
        raise ValueError("Macro file root must be an object")
    return MacroFile.from_dict(data)
