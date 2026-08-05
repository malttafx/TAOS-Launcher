# Adding Tools to Houdini — TAOS Launcher Payload

**The drive is the deploy.** Files copied into this folder reach every artist's
next Houdini launch. Nobody installs anything, ever.

## How the plumbing works

When an artist presses the Houdini button, the TAOS Launcher prepends this
folder's `packages\` to `HOUDINI_PACKAGE_DIR`:

```
<TAOSDRIVE>\pipeline\launcher\payloads\houdini\packages\
```

Houdini loads every package `.json` in there at startup — the native Houdini
packages mechanism, no hacks. Current resident: `taos.json` (sets
`TAOS_LOADED=1`; check inside Houdini with `hou.getenv("TAOS_LOADED")`).

## To add tools — extend the package

Houdini tools (HDAs, shelves, menus, python libs) ship as a **tools tree on
the drive** plus a `HOUDINI_PATH` entry in the package. Recommended layout:

```
<TAOSDRIVE>\pipeline\scripts\houdini\
├── otls\            .hda files
├── toolbar\         .shelf files
├── python3.11libs\  python modules (auto-importable)
└── MainMenuCommon.xml   menu additions (optional)
```

Then point `taos.json` at it (Houdini expands `$TAOSDRIVE` itself — the
launcher sets it before Houdini starts):

```json
{
    "env": [
        { "TAOS_LOADED": "1" }
    ],
    "path": "$TAOSDRIVE/pipeline/scripts/houdini"
}
```

`"path"` appends to `HOUDINI_PATH` the safe way (keeps `&` — the Houdini
defaults — intact). Forward slashes are correct in package files, even on
Windows.

**That's the deploy.** Once Google Drive finishes syncing, everyone's next
launch picks up new HDAs/shelves from the tools tree — the package file only
changes when you add a new *kind* of thing.

## Environment variables

- Package `"env"` entries are the Houdini-native way to add vars — prefer
  them over the launcher's `env.json` for anything Houdini-specific.
- `env.json` in this payload folder also works (launcher-side): `{TAOSDRIVE}`
  expands, but values **overwrite** the variable, they don't append. Never
  declare `HOUDINI_PATH` there — do it in the package with `"path"`.
- Inside Houdini you get for free: `TAOSDRIVE`, `TAOS_DCC` (= `houdini`),
  `TAOS_LAUNCHER_VERSION`, `TAOS_LOADED`.

## Pre-flight manifest

If a file is required for a valid launch, add it to
`payload_manifest.houdini` in `defaults.json` (launcher root on the drive).
The launcher then warns artists when it's missing.

## Rules of the road

- Warn, never block: a bad package or missing HDA should degrade to vanilla
  Houdini, not a startup error. Test package edits with
  `houdini -foreground` + check `hconfig` output for the expected paths.
- `$TAOSDRIVE` in packages, `hou.getenv("TAOSDRIVE")` in Python. NEVER
  hardcode `Q:\` — every machine mounts the drive at a different letter.
- This folder is LIVE for the whole crew. Package JSON syntax errors are
  silently skipped by Houdini — validate your JSON before copying up.
- HDAs on a cloud drive: keep them marked "Available offline" (whole
  launcher folder should already be) or first loads will stall on hydration.
- Announce tool drops in the pipeline channel.
