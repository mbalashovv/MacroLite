from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from macrolite.core.storage import MacroFile


def export_macro_exe(
    *,
    destination: str | Path,
    macro: MacroFile,
    loop_count: int,
    speed: float,
) -> None:
    destination_path = Path(destination)
    if destination_path.suffix.lower() != ".exe":
        destination_path = destination_path.with_suffix(".exe")

    with TemporaryDirectory(prefix="macrolite_export_") as tmp:
        tmp_path = Path(tmp)
        runner_path = tmp_path / "macrolite_macro_runner.py"
        runner_path.write_text(
            _runner_source(macro=macro, loop_count=loop_count, speed=speed),
            encoding="utf-8",
        )

        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--noconsole",
            "--clean",
            "--name",
            destination_path.stem,
            "--distpath",
            str(destination_path.parent),
            "--workpath",
            str(tmp_path / "build"),
            "--specpath",
            str(tmp_path),
            str(runner_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"PyInstaller export failed: {details}")


def _runner_source(*, macro: MacroFile, loop_count: int, speed: float) -> str:
    macro_json = json.dumps(macro.to_dict())
    return f'''\
from __future__ import annotations

import json
import threading
import time

import pyautogui
import pydirectinput
from pynput import keyboard

MACRO = json.loads({macro_json!r})
LOOP_COUNT = {loop_count}
SPEED = {speed!r}
STOP_EVENT = threading.Event()

KEY_ALIASES = {{
    "alt_l": "altleft",
    "alt_r": "altright",
    "caps_lock": "capslock",
    "ctrl_l": "ctrlleft",
    "ctrl_r": "ctrlright",
    "page_down": "pagedown",
    "page_up": "pageup",
    "win": "cmd",
    "shift_l": "shiftleft",
    "shift_r": "shiftright",
}}
for function_key in range(1, 13):
    KEY_ALIASES[f"f{{function_key}}"] = f"f{{function_key}}"


def normalize_key(key):
    name = getattr(key, "name", None)
    if name:
        return str(name)
    raw = str(key)
    if raw.startswith("Key."):
        return raw.removeprefix("Key.")
    return raw.strip("'")


def on_press(key):
    if normalize_key(key) == "f8":
        STOP_EVENT.set()
        return False
    return None


def sleep_interruptible(seconds):
    deadline = time.perf_counter() + seconds
    while time.perf_counter() < deadline:
        if STOP_EVENT.is_set():
            return True
        time.sleep(min(0.01, max(0.0, deadline - time.perf_counter())))
    return STOP_EVENT.is_set()


def execute(action):
    action_type = action["type"]
    if action_type == "mouse_move":
        pydirectinput.moveTo(action["x"], action["y"])
    elif action_type == "mouse_down":
        pydirectinput.moveTo(action["x"], action["y"])
        pydirectinput.mouseDown(button=to_pydirectinput_button(action.get("button")))
    elif action_type == "mouse_up":
        pydirectinput.moveTo(action["x"], action["y"])
        pydirectinput.mouseUp(button=to_pydirectinput_button(action.get("button")))
    elif action_type == "mouse_scroll":
        if "x" in action and "y" in action:
            pyautogui.moveTo(action["x"], action["y"])
        pyautogui.scroll(action.get("dy") or 0)
    elif action_type == "key_down":
        pydirectinput.keyDown(to_pydirectinput_key(action["key"]))
    elif action_type == "key_up":
        pydirectinput.keyUp(to_pydirectinput_key(action["key"]))


def to_pydirectinput_key(key):
    return KEY_ALIASES.get(key, key.lower() if len(key) == 1 else key)


def to_pydirectinput_button(button):
    if button in {{"left", "right", "middle"}}:
        return button
    return "left"


def play_once(actions):
    started_at = time.perf_counter()
    for action in actions:
        target_elapsed = float(action["time"]) / SPEED
        wait_time = max(0.0, target_elapsed - (time.perf_counter() - started_at))
        if sleep_interruptible(wait_time):
            return
        execute(action)


def main():
    pyautogui.PAUSE = 0
    pydirectinput.PAUSE = 0
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    actions = MACRO["actions"]
    iteration = 0
    while not STOP_EVENT.is_set() and (LOOP_COUNT == 0 or iteration < LOOP_COUNT):
        iteration += 1
        play_once(actions)


if __name__ == "__main__":
    main()
'''
