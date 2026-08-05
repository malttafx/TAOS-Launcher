# TAOS Launcher — v1 Spec

Status: APPROVED 2026-07-16 (Delcio) — v1 built same day
Owner: Delcio (design) / Claude (build)

Decisions locked on review:
- Env var name: **`TAOSDRIVE`** (no underscore)
- Locking an invalid path: **warning dialog explaining the problem, user
  chooses "Save anyway" or "Keep editing"** — never silent, never blocking
- Icons: Delcio's art in `icons/` (logo + per-DCC buttons)
- Google Drive "available offline": cannot be set programmatically (no
  public API) — launcher shows a one-time "available offline recommended"
  message with an Open-folder button instead; pre-flight reads also hydrate
  payload files as a side effect

---

## Tool name

`taos-launcher`

## Problem

Post-Ayon, nothing injects TAOS context into a DCC at startup. Every artist's
TAOS drive mounts at a different letter/path (Q:\, Z:\Arquivos Compartilhados\, …),
software lives in different places per machine, and per-DCC setup (env vars,
startup scripts, menus) is currently manual or absent. One small launcher fixes
path drift for the whole crew and becomes the delivery vehicle for future
pipeline tooling.

## Proposed approach

A single-window PySide6 app (per Delcio's mockup): TAOS drive field on top,
three DCC buttons (Maya, 3ds Max, Houdini), collapsible settings with per-DCC
path fields. **Thin shell + drive-side payloads:** the .exe only handles UI,
config, and launching. Everything that happens *on launch* (env setup, startup
scripts, future tools) lives as small per-DCC payload scripts on the TAOS drive
— updated by file copy, no reinstall ever.

## UI behavior (contract)

### Lock mechanic (drive field + each DCC path field)
- **Locked** = field grey / read-only. **Unlocked** = field white / editable.
- Locking a field validates the path and **saves to local config on lock**.
- Locking an invalid path: warning dialog explains exactly what's wrong;
  user chooses "Save anyway" (field tints red, saved to disk) or
  "Keep editing". Never blocks, never silent.
- **Reset to default** button per DCC field → re-reads current team default
  from the drive-side `defaults.json` (see Config).

### First run
- Drive field: **empty + unlocked**. DCC fields: prefilled with shipped
  defaults, **locked**.
- DCC buttons disabled until the drive path is set and reachable.

### Launch flow (per button press)
1. **Pre-flight check** — drive reachable, DCC exe exists, payload folder
   present, expected payload scripts present.
2. Problems → **warning dialog listing what's missing, with "Launch anyway."**
   Warn, never require. Missing payload = launch vanilla DCC.
3. Set environment: `TAOSDRIVE` (root path), `TAOS_LAUNCHER_VERSION`, plus
   whatever the payload's `env.json` declares.
4. Run the DCC's payload hook (startup script injection — see Payloads).
5. Launch the DCC executable, detached (launcher stays open).
6. Status strip: `Max 2026 launched · TAOS env OK` (or the warning summary).

### Tray
- Close button → minimize to tray (icon by the clock). Quit via tray menu.
- Tray right-click: Launch Maya / Launch Max / Launch Houdini / Open Launcher / Quit.
- "Start with Windows" = **opt-in checkbox** in settings (registry Run key).

## Config

| File | Location | Holds | Written by |
|---|---|---|---|
| `launcher_config.json` | `%APPDATA%\TAOS\` | drive path, custom DCC paths, lock states, tray/autostart prefs | the app, on lock |
| `defaults.json` | `<TAOSDRIVE>\pipeline\launcher\` | team-default DCC paths, payload manifest | us, by hand |
| Hardcoded fallback | inside the .exe | shipped DCC defaults (Maya 2026, Max 2026, Houdini 21.0) | build time |

Precedence: user config → drive defaults → hardcoded. Only the drive path
itself must be local (chicken-and-egg).

## Payloads (drive-side)

```
<TAOSDRIVE>\pipeline\launcher\
├── defaults.json
└── payloads\
    ├── maya\      env.json + userSetup injection hook
    ├── max\       env.json + startup-script hook
    └── houdini\   env.json + package/env hook
```

- Each payload = `env.json` (env vars to set) + optional startup hook the
  launcher wires in via the DCC's native mechanism (Maya: `PYTHONPATH`/
  `userSetup.py`; Max: `-U MAXScript` / startup dir; Houdini: `HOUDINI_PATH`
  package).
- **v1 payloads are minimal:** set `TAOSDRIVE` + declared env vars, print a
  "TAOS env loaded" confirmation inside the DCC. That's it. Menus, shelves,
  tools = later payload updates, zero launcher rebuilds.
- Pre-flight reads `defaults.json`'s manifest to know what "complete" looks
  like — so adding a required script later automatically joins the check.

## Inputs / outputs

| | Type | Source |
|---|---|---|
| Input | drive path, DCC paths | user via UI / configs |
| Input | payload scripts + defaults.json | TAOS drive |
| Output | running DCC with `TAOSDRIVE` env + payload applied | user's machine |
| Output | `launcher_config.json` | `%APPDATA%\TAOS\` |
| Output | session log | `%APPDATA%\TAOS\launcher.log` |

## Where it lives in the pipeline

Entry point for all DCC work, all crew. Source in `TAOS\pipeline\taos_launcher\`
(repo), built .exe distributed from `<TAOSDRIVE>\pipeline\launcher\dist\`.

## Alternatives considered

| Option | Pro | Con | Why not chosen |
|---|---|---|---|
| Ayon launcher | full context mgmt | just exited that complexity | vendor-exit decision 07-13 |
| .bat per DCC | zero build | no UI, no config, per-user hand-editing | doesn't fix path drift for 89 people |
| Python install + scripts | easy updates | Python setup on every crew machine | thin-shell exe + drive payloads gets same updatability |

## Dependencies

- Python 3.11 + PySide6 (build machine only — crew gets the .exe)
- PyInstaller (build)
- TAOS drive mounted (Google Drive) on each machine
- Icon art: `icons/` (logo + Maya/Max/Houdini buttons, from Delcio) —
  `build.bat` converts the logo PNG to .ico automatically

## Estimated setup cost

- Shell UI + lock/config/tray/pre-flight: **~1.5 days**
- v1 payloads (env-only, all three DCCs): **~0.5 day**
- PyInstaller packaging + first machine test: **~0.5 day**
- **Total: ~2.5 days to distributable v1.** Installer polish excluded (v1
  distribution = copy the .exe from the drive).

## Risk / failure modes

- **Drive not mounted / not synced** → pre-flight catches, buttons grey,
  status strip says why. Most common failure, fully handled.
- **Google Drive placeholder files** (cloud-only, not downloaded) → payload
  reads may stall. Mitigation: payload folder marked "available offline" —
  goes in the deploy note.
- **Stale payload edits via mount** — known Cowork mount staleness issue:
  verify payload files Windows-side after every deploy.
- **PyInstaller false-positive AV flags** on some machines — known Windows
  reality; mitigation: distribute from the shared drive, document the
  "allow" step.
- **Bus factor:** launcher source lives in the repo, payloads are plain
  scripts on the drive — anyone can edit payloads without touching the shell.

## Out of scope (v1)

- GridMarkets patch check (dropped while official Max 2026 fix is in flight)
- Shot/context picker, scene naming, project-per-shot setup
- Nuke / Blender buttons
- Auto-update of the .exe itself
- Installer with questions (installer stays dumb; first-run handles setup)
- Multiple versions per DCC

## How the director uses it (plain language)

Double-click the TAOS icon by the clock. First time only: tell it where your
TAOS drive lives and click the lock. From then on it's one click — press the
Max button and Max opens already knowing where TAOS lives, with whatever
tools we've published to the drive that week. When we improve the pipeline,
we drop new files on the drive and everyone's next launch picks them up —
nobody installs anything twice.

## How to run it

- Crew: copy `TAOS_Launcher.exe` from `<TAOSDRIVE>\pipeline\launcher\dist\`
  to desktop, run. Lives in tray after first close.
- Dev: `python taos_launcher\main.py` from the repo.
- Build: `build.bat` in `taos_launcher\` → produces the .exe via PyInstaller.
