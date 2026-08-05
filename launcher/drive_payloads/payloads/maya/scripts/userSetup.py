"""TAOS Maya payload — v1: confirm the TAOS environment loaded.

Future TAOS Maya tools (menus, shelves, Zoo config) get added here or imported
from sibling modules on the TAOS drive. Update by file copy — no reinstall.
"""
import os

import maya.utils


def _taos_hello():
    drive = os.environ.get("TAOSDRIVE", "<not set>")
    print("TAOS env loaded · TAOSDRIVE = %s" % drive)


maya.utils.executeDeferred(_taos_hello)
