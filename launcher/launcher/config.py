"""Config layer: local user config + drive-side defaults + hardcoded fallback.

Precedence when resolving a DCC path:
    user custom path (if set)  ->  drive defaults.json  ->  hardcoded fallback
Only the drive path itself must live locally (chicken-and-egg).
"""
import json
import os
import sys
import time
from pathlib import Path

APP_NAME = "TAOS Launcher"
ENV_VAR = "TAOSDRIVE"

# Relative location of launcher assets on the TAOS drive
LAUNCHER_REL = os.path.join("pipeline", "launcher")
PAYLOADS_REL = os.path.join(LAUNCHER_REL, "payloads")
DEFAULTS_REL = os.path.join(LAUNCHER_REL, "defaults.json")

DCCS = ["maya", "max", "houdini", "nuke"]
LABELS = {"maya": "Maya", "max": "3ds Max", "houdini": "Houdini", "nuke": "Nuke"}
EXES = {"maya": "maya.exe", "max": "3dsmax.exe", "houdini": "houdinifx.exe", "nuke": "Nuke16.0.exe"}

# Shipped fallback defaults (used when drive defaults.json is unreachable)
HARDCODED_DEFAULTS = {
    "maya": r"C:\Program Files\Autodesk\Maya2026\bin",
    "max": r"C:\Program Files\Autodesk\3ds Max 2026",
    "houdini": r"C:\Program Files\Side Effects Software\Houdini 21.0.440\bin",
    "nuke": r"C:\Program Files\Nuke16.0v8",
}

# What a "complete" payload looks like, if drive defaults.json doesn't say
BUILTIN_MANIFEST = {
    "maya": ["env.json", os.path.join("scripts", "userSetup.py")],
    "max": ["env.json", os.path.join("startup", "taos_startup.ms")],
    "houdini": ["env.json", os.path.join("packages", "taos.json")],
    "nuke": ["env.json", "init.py", "menu.py"],
}

CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "TAOS"
CONFIG_FILE = CONFIG_DIR / "launcher_config.json"
LOG_FILE = CONFIG_DIR / "launcher.log"


def resource_path(rel):
    """Path to a bundled resource — works in dev and inside the PyInstaller exe."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, rel)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), rel)


def log(msg):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except OSError:
        pass


def create_desktop_shortcut(exe_path):
    """Create/refresh a 'TAOS Launcher' shortcut on the user's Desktop,
    pointing at the launcher exe ON THE DRIVE (never a local copy - so
    every double-click runs the currently deployed version). Returns True
    on success. Uses the Windows Script Host COM object via PowerShell so
    OneDrive-redirected desktops resolve correctly."""
    if os.name != "nt" or not os.path.isfile(exe_path):
        return False
    try:
        import subprocess
        cmd = (
            "$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
            "[Environment]::GetFolderPath('Desktop')+'\\TAOS Launcher.lnk');"
            "$s.TargetPath='{exe}';"
            "$s.WorkingDirectory='{wd}';"
            "$s.IconLocation='{exe},0';"
            "$s.Description='TAOS Launcher - The Alchemy of a Storm pipeline';"
            "$s.Save()"
        ).format(exe=exe_path, wd=os.path.dirname(exe_path))
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-Command", cmd],
            capture_output=True, timeout=20, creationflags=0x08000000)
        ok = r.returncode == 0
        log("desktop shortcut %s -> %s" % ("created" if ok else "FAILED", exe_path))
        return ok
    except Exception as e:
        log("desktop shortcut error: %s" % e)
        return False


class Config:
    """User config, persisted to %APPDATA%\\TAOS\\launcher_config.json on lock."""

    def __init__(self):
        self.drive = ""
        self.drive_locked = False
        self.paths = {d: "" for d in DCCS}       # empty = use default
        self.locks = {d: True for d in DCCS}     # DCC fields ship locked
        self.autostart = False
        self.offline_msg_shown = False
        self.tray_msg_shown = False
        self.shortcut_created = False
        self._drive_defaults_cache = None
        self.load()

    # ---------- persistence ----------

    def load(self):
        if not CONFIG_FILE.exists():
            return  # first run
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            log("config load failed: %s" % e)
            return
        self.drive = data.get("drive", "")
        self.drive_locked = data.get("drive_locked", False)
        for d in DCCS:
            self.paths[d] = data.get("paths", {}).get(d, "")
            self.locks[d] = data.get("locks", {}).get(d, True)
        self.autostart = data.get("autostart", False)
        self.offline_msg_shown = data.get("offline_msg_shown", False)
        self.tray_msg_shown = data.get("tray_msg_shown", False)
        self.shortcut_created = data.get("shortcut_created", False)

    def save(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps({
                "drive": self.drive,
                "drive_locked": self.drive_locked,
                "paths": self.paths,
                "locks": self.locks,
                "autostart": self.autostart,
                "offline_msg_shown": self.offline_msg_shown,
                "tray_msg_shown": self.tray_msg_shown,
                "shortcut_created": self.shortcut_created,
            }, indent=2), encoding="utf-8")
        except OSError as e:
            log("config save failed: %s" % e)

    @property
    def first_run(self):
        return not CONFIG_FILE.exists()

    # ---------- drive-side defaults ----------

    def drive_ok(self):
        return bool(self.drive) and os.path.isdir(self.drive)

    def launcher_dir(self):
        return os.path.join(self.drive, LAUNCHER_REL) if self.drive else ""

    def payload_dir(self, dcc):
        return os.path.join(self.drive, PAYLOADS_REL, dcc) if self.drive else ""

    def drive_defaults(self, refresh=False):
        """Read team defaults.json from the drive. Cached per session."""
        if self._drive_defaults_cache is not None and not refresh:
            return self._drive_defaults_cache
        result = {}
        path = os.path.join(self.drive, DEFAULTS_REL) if self.drive else ""
        if path and os.path.isfile(path):
            try:
                result = json.loads(Path(path).read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                log("defaults.json unreadable: %s" % e)
        self._drive_defaults_cache = result
        return result

    def default_path(self, dcc):
        """Current team default for a DCC folder (drive first, hardcoded fallback)."""
        d = self.drive_defaults().get("dcc_defaults", {}).get(dcc)
        return d if d else HARDCODED_DEFAULTS[dcc]

    def manifest(self, dcc):
        m = self.drive_defaults().get("payload_manifest", {}).get(dcc)
        return m if m else BUILTIN_MANIFEST[dcc]

    # ---------- resolved values ----------

    def dcc_folder(self, dcc):
        return self.paths[dcc] if self.paths[dcc] else self.default_path(dcc)

    def exe_path(self, dcc):
        return os.path.join(self.dcc_folder(dcc), EXES[dcc])
