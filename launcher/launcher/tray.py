"""System tray icon: quick-launch menu next to the clock."""
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from . import __version__
from . import config as C


def create_tray(window, icon_path):
    tray = QSystemTrayIcon(QIcon(icon_path), window)
    tray.setToolTip("%s  v%s" % (C.APP_NAME, __version__))

    menu = QMenu()
    for dcc in C.DCCS:
        if not C.dcc_supported(dcc):
            continue
        act = QAction("Launch %s" % C.LABELS[dcc], menu)
        act.triggered.connect(lambda checked=False, d=dcc: window.launch_dcc(d))
        menu.addAction(act)
    menu.addSeparator()

    show_act = QAction("Open Launcher", menu)
    show_act.triggered.connect(window.show_from_tray)
    menu.addAction(show_act)

    quit_act = QAction("Quit", menu)
    quit_act.triggered.connect(window.quit_app)
    menu.addAction(quit_act)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: window.show_from_tray()
        if reason == QSystemTrayIcon.Trigger else None)
    tray.show()
    return tray
