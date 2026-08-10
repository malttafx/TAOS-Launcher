"""Main window: drive row, DCC buttons, collapsible settings, status strip."""
import os

from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QToolButton, QCheckBox, QMessageBox,
                               QSizePolicy, QLayout)

from . import __version__
from . import config as C
from . import dcc, preflight, autostart
from .splash import LaunchSplash
from .config import Config, resource_path, log
from .theme import STYLESHEET, repolish
from .tray import create_tray
from .widgets import LockField

ICON = {
    "logo": "icons/taos_launcher_logo.png",
    "maya": "icons/taos_launcher_maya_bt.png",
    "max": "icons/taos_launcher_max_bt.png",
    "houdini": "icons/taos_launcher_houdini_bt.png",
    "nuke": "icons/taos_launcher_nuke_bt.png",
}


class MainWindow(QMainWindow):
    def __init__(self, start_in_tray=False):
        super().__init__()
        self.cfg = Config()
        first_run = self.cfg.first_run

        self.setWindowTitle("TAOS - Launcher  ·  v%s" % __version__)
        self.setWindowIcon(QIcon(resource_path(ICON["logo"])))
        self.setStyleSheet(STYLESHEET)
        self.setMinimumWidth(430)
        self._quitting = False
        self._launch_splash = None

        self._build_ui()
        self.tray = create_tray(self, resource_path(ICON["logo"]))

        self._refresh_buttons()
        self.set_status("Ready" if self.cfg.drive_ok()
                        else "Set your TAOS drive path and click the lock to begin")
        # existing users (drive already configured) get the shortcut once too
        self._ensure_desktop_shortcut()

        if first_run:
            self.cfg.save()  # create the config file so first_run happens once

        if not start_in_tray:
            self.show()

    # ---------- UI assembly ----------

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 0)
        root.setSpacing(16)
        # Window always fits its content exactly — grows AND shrinks when
        # the settings panel toggles. (Qt never shrinks windows on its own.)
        root.setSizeConstraint(QLayout.SetFixedSize)

        # drive row — first run: empty + unlocked; after: as saved
        self.drive_field = LockField(
            "Taos drive:", placeholder=r"Q:\Shared drives\TAOS",
            locked=self.cfg.drive_locked,
            validator=lambda p: preflight.validate_folder(p),
            label_width=70)
        self.drive_field.setText(self.cfg.drive)
        self.drive_field.lockCommitted.connect(self._on_drive_locked)
        root.addWidget(self.drive_field)

        # DCC buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        btn_row.addStretch()
        self.dcc_buttons = {}
        for d in C.DCCS:
            b = QToolButton()
            b.setObjectName("dccBtn")
            b.setIcon(QIcon(resource_path(ICON[d])))
            b.setIconSize(QSize(96, 96))
            b.setToolTip("Launch %s" % C.LABELS[d])
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked=False, x=d: self.launch_dcc(x))
            btn_row.addWidget(b)
            self.dcc_buttons[d] = b
        btn_row.addStretch()
        root.addLayout(btn_row)

        # settings header (collapsible)
        self.settings_header = QToolButton()
        self.settings_header.setObjectName("settingsHeader")
        self.settings_header.setText("settings")
        self.settings_header.setCheckable(True)
        self.settings_header.setChecked(False)
        self.settings_header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.settings_header.setArrowType(Qt.DownArrow)
        self.settings_header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.settings_header.toggled.connect(self._toggle_settings)
        root.addWidget(self.settings_header)

        # settings panel
        self.settings_panel = QWidget()
        panel = QVBoxLayout(self.settings_panel)
        panel.setContentsMargins(0, 4, 0, 4)
        panel.setSpacing(10)

        title = QLabel("set default software path")
        title.setAlignment(Qt.AlignCenter)
        panel.addWidget(title)

        self.dcc_fields = {}
        for d in C.DCCS:
            f = LockField(
                "%s:" % C.LABELS[d],
                locked=self.cfg.locks[d], with_reset=True,
                validator=lambda p, x=d: preflight.validate_folder(p, C.EXES[x]),
                label_width=70)
            f.setText(self.cfg.paths[d] if self.cfg.paths[d] else self.cfg.default_path(d))
            f.lockCommitted.connect(lambda text, x=d: self._on_dcc_locked(x, text))
            f.resetRequested.connect(lambda x=d: self._on_dcc_reset(x))
            panel.addWidget(f)
            self.dcc_fields[d] = f

        self.autostart_cb = QCheckBox("Start with Windows (in tray)")
        self.autostart_cb.setChecked(self.cfg.autostart)
        self.autostart_cb.toggled.connect(self._on_autostart)
        panel.addWidget(self.autostart_cb)

        self.settings_panel.setVisible(False)
        root.addWidget(self.settings_panel)

        # status strip
        self.status = QLabel("")
        self.status.setObjectName("statusStrip")
        root.addWidget(self.status)

        self.setCentralWidget(central)
        # The constraint must also sit on the window's own layout — otherwise
        # only the content shrinks and the window shell keeps its old size.
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    # ---------- behavior ----------

    def _toggle_settings(self, open_):
        self.settings_panel.setVisible(open_)
        self.settings_header.setArrowType(Qt.UpArrow if open_ else Qt.DownArrow)

    def set_status(self, msg, level="ok"):
        self.status.setText(msg)
        self.status.setProperty("level", level)
        repolish(self.status)

    def _refresh_buttons(self):
        ok = self.cfg.drive_ok()
        for b in self.dcc_buttons.values():
            b.setEnabled(ok)

    def _on_drive_locked(self, text):
        self.cfg.drive = text
        self.cfg.drive_locked = True
        self.cfg._drive_defaults_cache = None  # re-read team defaults from new drive
        self.cfg.save()
        self._refresh_buttons()
        if self.cfg.drive_ok():
            self.set_status("TAOS drive saved")
            self._ensure_desktop_shortcut()
            self._maybe_offline_recommendation()
        else:
            self.set_status("Drive saved, but not reachable right now", "warn")

    def _on_dcc_locked(self, d, text):
        # storing empty means "use team default"
        self.cfg.paths[d] = "" if text == self.cfg.default_path(d) else text
        self.cfg.locks[d] = True
        self.cfg.save()
        self.set_status("%s path saved" % C.LABELS[d])

    def _on_dcc_reset(self, d):
        self.dcc_fields[d].setText(self.cfg.default_path(d))
        self.dcc_fields[d].mark_invalid(False)
        self.cfg.paths[d] = ""
        self.cfg.save()
        self.set_status("%s reset to team default" % C.LABELS[d])

    def _on_autostart(self, enabled):
        if autostart.set_autostart(enabled):
            self.cfg.autostart = enabled
            self.cfg.save()
        else:
            self.autostart_cb.setChecked(not enabled)
            self.set_status("Could not update Windows startup setting", "warn")

    def _ensure_desktop_shortcut(self):
        """One-time: put a 'TAOS Launcher' shortcut (targeting the exe on the
        drive) on the Desktop after the drive is configured. Flagged in config
        so a user who deletes the shortcut isn't nagged with a new one."""
        if self.cfg.shortcut_created or not self.cfg.drive_ok():
            return
        exe = os.path.join(self.cfg.launcher_dir(), "dist", "TAOS_Launcher.exe")
        if C.create_desktop_shortcut(exe):
            self.cfg.shortcut_created = True
            self.cfg.save()
            self.set_status("Ready · TAOS Launcher shortcut added to your Desktop")

    def _maybe_offline_recommendation(self):
        if self.cfg.offline_msg_shown:
            return
        self.cfg.offline_msg_shown = True
        self.cfg.save()
        box = QMessageBox(self)
        box.setWindowTitle("Recommended: offline access")
        box.setIcon(QMessageBox.Information)
        box.setText("Available offline recommended.")
        box.setInformativeText(
            "In Google Drive, right-click the folder below and choose\n"
            "Offline access → Available offline, so launches never wait on sync:\n\n"
            "%s" % (self.cfg.launcher_dir() or self.cfg.drive))
        open_btn = box.addButton("Open folder", QMessageBox.ActionRole)
        box.addButton("OK", QMessageBox.AcceptRole)
        box.exec()
        if box.clickedButton() is open_btn:
            target = self.cfg.launcher_dir()
            if not os.path.isdir(target):
                target = self.cfg.drive
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    # ---------- launching ----------

    def launch_dcc(self, d):
        warnings = preflight.check_dcc(self.cfg, d)
        if warnings:
            box = QMessageBox(self)
            box.setWindowTitle("Pre-flight — %s" % C.LABELS[d])
            box.setIcon(QMessageBox.Warning)
            box.setText("Some checks did not pass:")
            box.setInformativeText("\n\n".join(warnings))
            cont = box.addButton("Launch anyway", QMessageBox.AcceptRole)
            box.addButton("Cancel", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() is not cont:
                self.set_status("%s launch cancelled" % C.LABELS[d], "warn")
                return
        ok, msg, proc = dcc.launch(self.cfg, d)
        if ok and warnings:
            msg += " · %d warning(s), see log" % len(warnings)
            log("launched %s with warnings: %s" % (d, " | ".join(warnings)))
        self.set_status(msg, "ok" if ok else "error")
        if ok and proc is not None:
            # branded boot splash - drawn by this process so it stays painted
            # while the DCC's own UI thread is busy loading plugins
            # per-DCC art first (taos_splash_max.png etc.), generic fallback
            splash_dir = os.path.join(self.cfg.drive, "pipeline", "launcher",
                                      "splash")
            art = None
            for name in ("taos_splash_%s.png" % d, "taos_splash.png"):
                cand = os.path.join(splash_dir, name)
                if os.path.isfile(cand):
                    art = cand
                    break
            self._launch_splash = LaunchSplash(
                d, C.LABELS[d], proc, resource_path(ICON["logo"]),
                art_path=art, splash_dir=splash_dir)

    # ---------- tray / lifecycle ----------

    def show_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self._quitting = True
        self.tray.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self._quitting:
            event.accept()
            return
        event.ignore()
        self.hide()
        if not self.cfg.tray_msg_shown:
            self.cfg.tray_msg_shown = True
            self.cfg.save()
            self.tray.showMessage(
                C.APP_NAME,
                "Still running here — right-click for quick launch, Quit to exit.")
