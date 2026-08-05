# TAOS Launcher — pipeline TD handoff

**Current shipped version: v1.3.1** (deployed 2026-07-18)
Source of truth for this tool: `D:\ClaudeAi\TAOS\pipeline\taos_launcher\` (this folder).
Design contract: `SPEC.md` · Ops/behaviour: `README.md` · This file: how to own, version and ship it.

---

## 1. What it is, in one paragraph

Post-Ayon, nothing injected TAOS context into a DCC at startup. The launcher is a
**thin PySide6 shell compiled to a single .exe** whose only jobs are: remember where
this artist's TAOS drive is mounted, set `TAOSDRIVE` + per-DCC env, wire the DCC's
native startup mechanism at the payload folder on the drive, and launch the DCC
detached. **Everything a launch actually *does* lives on the drive**, not in the exe —
so changing pipeline behaviour is a file copy to `Q:`, never a rebuild and never a
crew reinstall. The exe only changes when the *shell* changes (UI, launch logic,
splash mechanics, config).

DCC wiring: Maya → `PYTHONPATH` + `userSetup.py` · Max → `ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR`
· Houdini → `HOUDINI_PACKAGE_DIR`.

---

## 2. What you need to build

| | |
|---|---|
| OS | Windows (PyInstaller builds per-platform; the exe is Windows-only) |
| Python | 3.11+ on PATH. 3.14 verified working on Delcio's box (07-18) |
| Deps | none to install by hand — `build.bat` makes `.venv` and pulls PySide6 / PyInstaller / Pillow |
| Drive | TAOS drive mounted, write access to `<TAOSDRIVE>\pipeline\` |

`run_dev.bat` runs the UI from source without building — use it for everything except
the final release check.

---

## 3. Versioning — the whole procedure

**The version has exactly one home:** `launcher\__init__.py` → `__version__`.
Nothing else hardcodes it. Never edit the version anywhere else.

```
release.bat 1.3.2        bump -> build -> deploy to the drive (asks before copying)
release.bat              build + deploy the current version, no bump
python bump_version.py 1.3.2     bump only
python bump_version.py --print   what version is this source tree?
```

`release.bat` does, in order: bump → `build.bat` (venv, deps, .ico, version stamp,
PyInstaller) → resolve the drive (`TAOSDRIVE` env → your launcher config → ask) →
kill any running launcher → archive the drive's current exe to
`dist\_archive\TAOS_Launcher_v<old>.exe` → copy the new exe to **both** deploy targets →
write `VERSION.txt` → verify both copies match the build by byte size. It aborts
without touching the drive if anything upstream fails.

**Where the version surfaces** (all fed from `__init__.py`):

| Surface | Why it matters |
|---|---|
| Launcher title bar `TAOS - Launcher · v1.3.1` | **first question on any support ping** — "what does your title bar say?" |
| Tray tooltip | same, when it's minimised |
| `TAOS_LAUNCHER_VERSION` env inside every DCC | tools can branch or log on it |
| exe file properties (Details → File version) | tells you what a copy on someone's desktop actually is, without running it |
| `<TAOSDRIVE>\pipeline\launcher\dist\VERSION.txt` | what's currently shipped, readable by anyone |

The exe-properties stamp is new in this handoff (`make_version_info.py`, wired into
`build.bat`) — v1.3.1 and earlier carry no file-version metadata, so a stray old copy
will show blank there. That alone is a reason to cut a rebuild early.

**Convention:** patch = shell fix/tuning · minor = new shell feature or UI change ·
payload/defaults/splash-art changes **do not bump the exe** (they aren't in it).

---

## 4. Deploy targets — there are two, keep them identical

| Path | Who uses it |
|---|---|
| `<TAOSDRIVE>\pipeline\launcher\dist\TAOS_Launcher.exe` | documented crew copy point; the README install instruction |
| `<TAOSDRIVE>\pipeline\TAOS_Launcher.exe` | what the auto-created desktop shortcuts point at |

Both are currently 46,483,186 bytes, mtime 2026-07-18 09:43 — in sync. `release.bat`
writes both. If you ever copy by hand, copy both, or half the crew keeps running the
old build with no symptom other than a stale title bar.

Drive-side layout the exe expects:

```
<TAOSDRIVE>\pipeline\launcher\
├── defaults.json                     team default DCC paths + payload manifest
├── Create_Desktop_Shortcut.bat       manual fallback for the shortcut
├── dist\TAOS_Launcher.exe            crew copy point (+ VERSION.txt, _archive\)
├── payloads\{maya,max,houdini}\      what a launch DOES  <-- edit here, no rebuild
└── splash\  taos_splash_<dcc>.png + splash_config.json
```

`drive_payloads\` in this repo is the **template** for that tree, not the live copy.
The live drive files are ahead of it in places (splash art, tuned config) — never
blind-robocopy the repo over the drive.

---

## 5. What does NOT need a rebuild

Highest-value thing to internalise:

| Change | Where |
|---|---|
| What happens inside a DCC at startup (menus, tools, env) | `payloads\<dcc>\` on the drive |
| Team default software paths, required payload files | `defaults.json` on the drive |
| Splash size/position per DCC | `splash\splash_config.json` on the drive — physical px `{w,h,x,y}`, edit + relaunch the DCC |
| Splash artwork | `splash\taos_splash_<dcc>.png` on the drive (2× the DCC's splash footprint, no baked text, semi-transparent bottom strip so "Loading plug-in…" reads through) |

Rebuild only for: UI/window changes, launch or pre-flight logic, splash *mechanics*
(`launcher\splash.py`), config schema, tray/autostart, single-instance behaviour.

---

## 6. Traps (all of these have bitten already)

- **Copy fails, "file in use"** — someone has the drive exe running; it locks it.
  `release.bat` taskkills locally first, but a crew member on another machine can
  still hold it. Ask in Discord, then retry.
- **Newest launcher wins** — `main.py` taskkills every other `TAOS_Launcher.exe` on
  startup. Intentional (stateless app, DCCs spawn detached) — don't "fix" it, but know
  that a crew member's tray icon can vanish when they open a newer copy.
- **SmartScreen / AV false positives** on a fresh unsigned PyInstaller exe. Expected.
  Distribute from the drive, walk the artist through "More info → Run anyway". Pilot
  a release with 2–3 people before announcing it.
- **Google Drive placeholders** — payload reads stall if the folder isn't
  "available offline". The launcher recommends it once per artist; there's no API to
  set it. Give sync a minute after a deploy before telling anyone to relaunch.
- **Houdini splash geometry is a guess** — `{1030,580,x0,y20}` was never
  pixel-verified ("lower and much bigger" was the note). Max/Maya y-values are
  verified; the `x=+1` nudge is not. Fix in the json, not in code.
- **PyInstaller rewrites `TAOS_Launcher.spec`** on every CLI build. It's a build
  artifact, not config — `build.bat` drives the flags.
- **`.venv\`, `build\`, `dist\` are local** and excluded from the handoff zip;
  `build.bat` recreates them.
- **Editing this source over a network mount can serve stale reads.** After any
  remote edit, verify Windows-side before you build.

---

## 7. Out of scope by decision (don't rebuild these back in)

Auto-update of the exe · installer with questions (installer stays dumb, first-run
handles setup) · shot/context picker · Nuke/Blender buttons · multiple versions per
DCC · GridMarkets patch check. Full rationale in `SPEC.md`.

Ruled and not up for re-litigation: env var is **`TAOSDRIVE`** (no underscore);
locks **warn, never block**; behaviour ships as drive payloads, never as a reinstall.

---

## 8. Ownership

Design decisions: Delcio. Build, release and drive deploy: pipeline TD (you).
Payload content: whoever owns that DCC's tooling — they never need you to rebuild.
