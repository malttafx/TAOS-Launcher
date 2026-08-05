"""TAOS Launcher entry point.

Dev:    python main.py            (window)
        python main.py --tray     (start minimized to tray)
Build:  build.bat  ->  dist/TAOS_Launcher.exe
"""
import os
import subprocess
import sys

from PySide6.QtWidgets import QApplication

from launcher.mainwindow import MainWindow

CREATE_NO_WINDOW = 0x08000000


def _kill_older_instances():
    """Newest launcher wins. If any other TAOS_Launcher.exe is running
    (e.g. an older version parked in the tray), close it before we start -
    otherwise crew end up with a stale exe answering the tray clicks.
    The launcher is stateless (config saved on every change) and DCCs are
    spawned fully detached, so force-closing an old instance loses nothing.
    """
    if os.name != "nt":
        return
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "TAOS_Launcher.exe",
             "/FI", "PID ne %d" % os.getpid()],
            capture_output=True, timeout=10,
            creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass  # never block startup on cleanup


def run():
    _kill_older_instances()
    app = QApplication(sys.argv)
    app.setApplicationName("TAOS Launcher")
    app.setQuitOnLastWindowClosed(False)  # lives in the tray
    win = MainWindow(start_in_tray="--tray" in sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
