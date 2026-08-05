"""Set (or print) the TAOS Launcher version.

The version has exactly one home: launcher/__init__.py -> __version__.
Everything else reads it from there (title bar, tray tooltip,
TAOS_LAUNCHER_VERSION env inside the DCCs, the exe's Windows file
properties, VERSION.txt on the drive).

Usage:
    python bump_version.py 1.3.2      set the version
    python bump_version.py --print    print the current version
"""
import re
import sys
from pathlib import Path

INIT = Path(__file__).resolve().parent / "launcher" / "__init__.py"
PATTERN = re.compile(r'(__version__\s*=\s*")([^"]+)(")')


def current():
    m = PATTERN.search(INIT.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("ERROR: no __version__ found in %s" % INIT)
    return m.group(2)


def main(argv):
    if not argv or argv[0] in ("--print", "-p"):
        print(current())
        return 0

    new = argv[0].lstrip("vV")
    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        raise SystemExit("ERROR: version must look like 1.3.2 (got %r)" % new)

    old = current()
    if old == new:
        print("version already %s - nothing to do" % new)
        return 0

    text = INIT.read_text(encoding="utf-8")
    INIT.write_text(PATTERN.sub(lambda m: m.group(1) + new + m.group(3), text, count=1),
                    encoding="utf-8")
    print("version %s -> %s" % (old, new))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
