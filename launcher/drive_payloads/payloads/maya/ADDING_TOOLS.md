# Adding Tools to Maya — TAOS Launcher Payload

**The drive is the deploy.** Files copied into this folder reach every artist's
next Maya launch. Nobody installs anything, ever.

## How the plumbing works

When an artist presses the Maya button, the TAOS Launcher prepends this
folder's `scripts\` to `PYTHONPATH`:

```
<TAOSDRIVE>\pipeline\launcher\payloads\maya\scripts\
```

Maya runs the `userSetup.py` in there at startup. Native Maya behavior, no
hacks. Everything in `scripts\` is importable inside Maya; everything in
`userSetup.py` runs on launch.

## To add a tool — 3 steps

1. **Drop your module** into `scripts\` — a single `taos_mytool.py` or a
   package folder. It's on `PYTHONPATH`, so it's importable immediately.

2. **Hook it in `userSetup.py`** — deferred, and wrapped so it can NEVER
   break Maya startup:

   ```python
   def _load_taos_tools():
       try:
           import taos_mytool
           taos_mytool.build_menu()
       except Exception as e:
           print("TAOS: tool failed to load — %s" % e)

   maya.utils.executeDeferred(_load_taos_tools)
   ```

   Warn, never block — same philosophy as the launcher. A broken tool prints
   a complaint; it does not take Maya down with it.

3. **That's the deploy.** Once Google Drive finishes syncing, everyone's next
   launch picks it up. Verify the file landed on a second machine before
   calling it shipped — Drive sync lag is real.

## Environment variables

- `env.json` in this folder: anything in its `"env"` block is set at launch.
  `{TAOSDRIVE}` expands to the artist's drive path.
- ⚠️ Declared values **overwrite** the variable, they don't append. Don't
  declare `PYTHONPATH` or `MAYA_MODULE_PATH` here without including what
  you'd be stomping.
- Inside Maya you get for free: `TAOSDRIVE`, `TAOS_DCC` (= `maya`),
  `TAOS_LAUNCHER_VERSION`.

## Pre-flight manifest

If your tool is required for a valid launch, add its files to
`payload_manifest.maya` in `defaults.json` (launcher root on the drive). The
launcher then warns artists when it's missing.

## Rules of the road

- Keep `userSetup.py` thin — it's an importer, not a home for tool code.
  Real logic lives in sibling modules.
- `os.environ["TAOSDRIVE"]` for anything on the drive. NEVER hardcode `Q:\` —
  every machine mounts the drive at a different letter; that's the entire
  reason the launcher exists.
- This folder is LIVE for the whole crew. Test in your own Maya first
  (`sys.path.insert` + import in the Script Editor), then copy up.
- Announce tool drops in the pipeline channel so people know why a new menu
  appeared.
