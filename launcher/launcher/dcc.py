"""Per-DCC launch wiring. The shell only sets env + points each DCC at its
payload folder on the TAOS drive; the payload does the rest.

Wiring per DCC (native startup mechanisms, no hacks):
  maya    -> payload/scripts prepended to PYTHONPATH (userSetup.py runs)
  max     -> ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR = payload/startup
  houdini -> payload/packages prepended to HOUDINI_PACKAGE_DIR
"""
import json
import os
import subprocess

from . import __version__
from . import config as C
from .config import log

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200


def _prepend(env, key, value):
    old = env.get(key, "")
    env[key] = value + (os.pathsep + old if old else "")


def build_env(cfg, dcc):
    env = dict(os.environ)
    env[C.ENV_VAR] = cfg.drive
    env["TAOS_LAUNCHER_VERSION"] = __version__
    env["TAOS_DCC"] = dcc

    pdir = cfg.payload_dir(dcc)
    if os.path.isdir(pdir):
        # payload-declared env vars ({TAOSDRIVE} expands to the drive path)
        env_json = os.path.join(pdir, "env.json")
        if os.path.isfile(env_json):
            try:
                with open(env_json, "r", encoding="utf-8") as f:
                    declared = json.load(f).get("env", {})
                for k, v in declared.items():
                    env[k] = str(v).replace("{%s}" % C.ENV_VAR, cfg.drive)
            except (OSError, ValueError) as e:
                log("env.json unreadable for %s: %s" % (dcc, e))

        # startup-hook wiring
        if dcc == "maya":
            _prepend(env, "PYTHONPATH", os.path.join(pdir, "scripts"))
        elif dcc == "max":
            env["ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR"] = os.path.join(pdir, "startup")
        elif dcc == "houdini":
            _prepend(env, "HOUDINI_PACKAGE_DIR", os.path.join(pdir, "packages"))
        elif dcc == "nuke":
            _prepend(env, "NUKE_PATH", pdir)
    return env


def launch(cfg, dcc):
    """Launch detached. Returns (ok, status_message, process_or_None).

    The process handle only drives the launch splash (window watch +
    early-exit detection); the DCC still runs fully detached.
    """
    exe = cfg.exe_path(dcc)
    try:
        kwargs = {
            "env": build_env(cfg, dcc),
            "cwd": os.path.dirname(exe) if os.path.isdir(os.path.dirname(exe)) else None,
            "close_fds": True,
        }
        if os.name == "nt":
            kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        proc = subprocess.Popen([exe], **kwargs)
    except OSError as e:
        log("launch failed %s: %s" % (dcc, e))
        return False, "%s failed to launch: %s" % (C.LABELS[dcc], e), None
    log("launched %s (%s)" % (dcc, exe))
    return True, "%s launched · TAOS env OK" % C.LABELS[dcc], proc
