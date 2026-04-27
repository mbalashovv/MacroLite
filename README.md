# MacroLite

MacroLite is a lightweight Windows desktop app for recording and replaying mouse and keyboard actions.

It is designed for simple repetitive desktop tasks: record what you do once, then replay it later once, multiple times, or continuously until stopped. Playback uses a DirectInput-based backend for keyboard input, mouse movement, and mouse clicks.

## Download

Download the latest Windows `.exe` from the GitHub releases page:

[Download MacroLite](https://github.com/mbalashovv/MacroLite/releases/latest)

## Features

- Record mouse movement, clicks, scrolling, and keyboard input.
- Replay recorded macros once or for a selected number of loops.
- Run continuous playback until stopped.
- Save and load macro files as `.macro.json`.
- Export recorded macros as standalone `.exe` files.
- Use DirectInput-based playback for keyboard and mouse actions.
- Use `F8` to start or stop recording.
- Use `F12` to start or stop playback.
- Simple Windows desktop interface.

## Use Cases

- Repeating clicks and keyboard input in desktop applications.
- Automating simple browser or file explorer workflows.
- Replaying repetitive form-filling or data-entry steps.
- Testing simple input playback in apps that ignore standard simulated input.
- Sharing recorded macros with other Windows users.
- Running small local automations without a full RPA tool.

## Notes

MacroLite uses absolute screen coordinates. For best results, keep the target window in the same position and size when replaying a macro. Windowed mode is usually more reliable than fullscreen mode.

Some applications may still block simulated input, especially games, anti-cheat protected software, remote desktop sessions, or elevated/admin windows. If an elevated/admin app is the target, MacroLite may also need to be run as administrator.
