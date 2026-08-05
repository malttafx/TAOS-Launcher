"""Pre-flight checks. Everything returns warnings — nothing here ever blocks.

The manifest of what a 'complete' payload looks like comes from the drive-side
defaults.json, so adding a required script later automatically joins the check
without rebuilding the exe.
"""
import os

from . import config as C


def check_drive(cfg):
    warnings = []
    if not cfg.drive:
        warnings.append("TAOS drive path is not set.")
    elif not os.path.isdir(cfg.drive):
        warnings.append("TAOS drive not reachable: %s\n"
                        "(Is Google Drive mounted and synced?)" % cfg.drive)
    return warnings


def check_dcc(cfg, dcc):
    """Warnings for one DCC launch. Empty list = all clear."""
    warnings = list(check_drive(cfg))

    exe = cfg.exe_path(dcc)
    if not os.path.isfile(exe):
        warnings.append("%s executable not found:\n%s" % (C.LABELS[dcc], exe))

    if cfg.drive_ok():
        pdir = cfg.payload_dir(dcc)
        if not os.path.isdir(pdir):
            warnings.append("Payload folder missing on the TAOS drive:\n%s\n"
                            "(%s will launch without TAOS setup.)" % (pdir, C.LABELS[dcc]))
        else:
            missing = [f for f in cfg.manifest(dcc)
                       if not os.path.isfile(os.path.join(pdir, f))]
            if missing:
                warnings.append("Payload files missing for %s:\n  - %s" %
                                (C.LABELS[dcc], "\n  - ".join(missing)))
    return warnings


def validate_folder(path, must_contain=None):
    """Used by the lock mechanic. Returns None if fine, else a description."""
    if not path:
        return "Path is empty."
    if not os.path.isdir(path):
        return "Folder does not exist:\n%s" % path
    if must_contain and not os.path.isfile(os.path.join(path, must_contain)):
        return "Folder exists but does not contain %s:\n%s" % (must_contain, path)
    return None
