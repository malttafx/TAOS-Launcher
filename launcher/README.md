# TAOS Launcher

One window, three buttons. Sets `TAOSDRIVE` and per-DCC TAOS setup at launch.
Thin shell (.exe) + drive-side payloads: updating what a launch *does* is a
file copy to the TAOS drive — nobody reinstalls anything.

See `SPEC.md` for the full design contract and `HANDOFF.md` for the
build/version/deploy procedure (pipeline TD ownership doc).

## Folder map

| Path | What |
|---|---|
| `main.py` | Entry point (`--tray` starts minimized) |
| `launcher/config.py` | Local config + drive defaults + fallback resolution |
| `launcher/widgets.py` | Lock-field mechanic (grey locked / white editable) |
| `launcher/preflight.py` | Warn-never-block checks before launch |
| `launcher/dcc.py` | Env + startup wiring per DCC, detached launch |
| `launcher/mainwindow.py` | UI assembly, launch flow, offline recommendation |
| `launcher/tray.py`, `launcher/autostart.py` | Tray menu, opt-in Windows startup |
| `drive_payloads/` | **Template for the TAOS drive** — copy to `<TAOSDRIVE>\pipeline\launcher\` |
| `icons/` | Logo + DCC button art (from Delcio's mock) |
| `build.bat`, `make_ico.py`, `make_version_info.py` | One-command exe build (+ version stamp) |
| `release.bat`, `bump_version.py`, `drive_path.py` | Bump version, build, deploy to the drive |
| `HANDOFF.md` | Owner doc: versioning, deploy targets, traps |

## Run (dev)

    pip install PySide6
    python main.py

## Build the exe

    build.bat            → dist\TAOS_Launcher.exe

## Cut a new version

    release.bat 1.3.2    bump → build → deploy to both drive targets

Version lives in one place only: `launcher\__init__.py` → `__version__`.
See `HANDOFF.md`.

## Deploy (first time)

1. Copy `drive_payloads\*` → `<TAOSDRIVE>\pipeline\launcher\`
   (so it contains `defaults.json` and `payloads\maya|max|houdini\...`)
2. Copy `dist\TAOS_Launcher.exe` → `<TAOSDRIVE>\pipeline\launcher\dist\`
3. Crew: copy the exe anywhere local (desktop is fine) and run it.
   First run: set your TAOS drive path, click the lock. Done.
4. Recommend (the app also prompts this once): right-click
   `<TAOSDRIVE>\pipeline\launcher` in Google Drive → Offline access →
   **Available offline**. There is no reliable way to set this
   programmatically, so the launcher shows the recommendation + opens the
   folder for you instead.

## Update workflows

| Change | How |
|---|---|
| What a launch does (env, menus, tools) | Edit files in `<TAOSDRIVE>\pipeline\launcher\payloads\<dcc>\` — everyone's next launch picks it up |
| Team default software paths | Edit `defaults.json` on the drive |
| Require a new payload file in pre-flight | Add it to `payload_manifest` in `defaults.json` |
| Splash size/position per DCC | Edit `splash\splash_config.json` on the drive — no rebuild |
| The shell itself (UI, launch logic) | Edit source here, run `release.bat <new version>` — bumps, builds and deploys both drive copies |

## DCC wiring (native startup mechanisms)

- **Maya** — payload `scripts\` is prepended to `PYTHONPATH`; `userSetup.py` runs.
- **3ds Max** — `ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR` points at payload `startup\`.
- **Houdini** — payload `packages\` is prepended to `HOUDINI_PACKAGE_DIR`.

All three receive `TAOSDRIVE`, `TAOS_DCC`, `TAOS_LAUNCHER_VERSION`, plus
anything declared in the payload's `env.json` (`{TAOSDRIVE}` expands).

## Config & logs

- User config: `%APPDATA%\TAOS\launcher_config.json` (written on lock)
- Log: `%APPDATA%\TAOS\launcher.log`
