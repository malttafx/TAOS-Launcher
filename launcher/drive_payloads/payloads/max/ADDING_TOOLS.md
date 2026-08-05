# Adding Tools to 3ds Max — TAOS Launcher Payload

**The drive is the deploy.** Files copied into this folder reach every artist's
next Max launch. Nobody installs anything, ever.

## How the plumbing works

When an artist presses the Max button, the TAOS Launcher sets:

```
ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR = <TAOSDRIVE>\pipeline\launcher\payloads\max\startup\
```

Max runs **every `.ms` file** in that `startup\` folder at launch. Native Max
mechanism, no hacks. Current residents: `taos_startup.ms` (env confirmation),
`taos_welcome.ms` (welcome-card shim), `taos_template_loader.ms`.

## To add a tool — 2 steps

1. **Drop a `.ms` shim** into `startup\`. Keep it tiny — the shim's only job
   is to hand off to the real tool living elsewhere on the drive. Copy the
   pattern from `taos_welcome.ms`:

   ```maxscript
   (
       try (
           local taosDrive = systemTools.getEnvVariable "TAOSDRIVE"
           if taosDrive != undefined and taosDrive != "" do (
               local tool = taosDrive + @"\pipeline\scripts\3dsmax\my_tool.py"
               if (doesFileExist tool) do python.ExecuteFile tool
           )
       ) catch (
           format "TAOS: my_tool skipped (%)\n" (getCurrentException())
       )
   )
   ```

   Warn, never block — everything in `try/catch`, silent skip on render
   nodes (`IsNetServer()`) and quiet mode (`GetQuietMode()`) if the tool has
   UI. A broken tool prints a complaint; it does not take Max down.

2. **That's the deploy.** Once Google Drive finishes syncing, everyone's next
   launch picks it up. Verify the file landed on a second machine before
   calling it shipped — Drive sync lag is real.

## Max 2026 gotchas

- Python **3.11** + **PySide6** (PySide2 is gone — imports of it fail).
- Menus: `menuMan` is dead for the new system — register menus via the
  `cuiRegisterMenus` callback instead.
- Toolbars live in Customize UI; menus in the Menu Editor system.

## Environment variables

- `env.json` in this folder: anything in its `"env"` block is set at launch.
  `{TAOSDRIVE}` expands to the artist's drive path.
- ⚠️ Declared values **overwrite** the variable, they don't append.
- Inside Max you get for free: `TAOSDRIVE`, `TAOS_DCC` (= `max`),
  `TAOS_LAUNCHER_VERSION`.

## Pre-flight manifest

If your tool is required for a valid launch, add its files to
`payload_manifest.max` in `defaults.json` (launcher root on the drive). The
launcher then warns artists when it's missing.

## Rules of the road

- Shims in `startup\` stay thin; real logic lives in
  `<TAOSDRIVE>\pipeline\scripts\3dsmax\` — updatable without touching the
  payload.
- Read `TAOSDRIVE` from the environment. NEVER hardcode `Q:\` — every machine
  mounts the drive at a different letter.
- This folder is LIVE for the whole crew. Test locally first (run your shim
  from the Scripting Listener), then copy up.
- Announce tool drops in the pipeline channel.
