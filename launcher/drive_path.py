"""Print the TAOS drive root this machine's launcher is configured with.

Reads %APPDATA%\\TAOS\\launcher_config.json (written by the launcher when you
lock the drive field). Prints nothing if it isn't set - release.bat then falls
back to the TAOSDRIVE env var or asks.
"""
import json
import os
from pathlib import Path

cfg = Path(os.environ.get("APPDATA", str(Path.home()))) / "TAOS" / "launcher_config.json"
drive = ""
if cfg.is_file():
    try:
        drive = json.loads(cfg.read_text(encoding="utf-8")).get("drive", "") or ""
    except (OSError, ValueError):
        drive = ""
print(drive.rstrip("\\/"))
