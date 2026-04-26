# MacroLite

MacroLite is a lightweight Windows desktop macro recorder. It records mouse and keyboard actions, saves them as JSON, and replays them once or in a loop.

## Requirements

- Windows 10 or Windows 11
- Python 3.12+
- pip

## Install

```bash
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Run

```bash
macrolite
```

Alternative without installing the console command:

```bash
python -m macrolite
```

## Current MVP Scope

- GUI-first desktop application.
- Record mouse movement, clicks, scrolls, and keyboard press/release events.
- Save and load `.macro.json` files.
- Export macro playback as a standalone `.exe`.
- Replay macros with loop count or continuous playback.
- Use `F8` to start/stop recording.
- Use `F12` to start/stop playback.

## Notes

MacroLite uses absolute screen coordinates. Keep the target window in the same position and size when replaying a macro.
