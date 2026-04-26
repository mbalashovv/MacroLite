from __future__ import annotations

from macrolite.core.actions import MacroAction


def compress_mouse_moves(actions: list[MacroAction]) -> list[MacroAction]:
    compressed: list[MacroAction] = []
    last_move_position: tuple[int | None, int | None] | None = None

    for action in actions:
        if action.type != "mouse_move":
            compressed.append(action)
            last_move_position = None
            continue

        position = (action.x, action.y)
        if position == last_move_position:
            continue
        compressed.append(action)
        last_move_position = position

    return compressed
