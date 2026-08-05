"""TAOS launch splash — the branded card shown while a DCC boots.

Drawn by the LAUNCHER process (own event loop), so it stays painted while
the DCC's UI thread is blocked loading plugins — an in-DCC window cannot do
this (its paint events starve until boot completes). Same architecture AYON
uses for its launch splash.

Lifecycle: appears on launch click -> rides on top during boot -> the DCC's
real main window appears -> short hold -> closes. Click dismisses instantly.
Hard timeout guarantees it never outstays a hung boot. Never steals focus,
so license dialogs and error prompts behave normally.
"""
import ctypes
from ctypes import wintypes

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QVBoxLayout,
                               QWidget)

from .config import log

POLL_MS = 500          # window-watch cadence
HOLD_MS = 2500         # linger after the DCC window appears
TIMEOUT_MS = 240000    # absolute cap (4 min) — never outlive a hung boot
EARLY_EXIT_GRACE_MS = 3000  # if the DCC process dies, close shortly after
# Native DCC boot splashes are fixed-size bitmaps (~860x532 PHYSICAL px,
# roughly screen-centered, not DPI-aware). The card cover-fits that
# footprint / devicePixelRatio. Per-DCC calibration (w, h, y nudge) lives
# DRIVE-SIDE in splash\splash_config.json next to the art - edit + relaunch
# the DCC, no rebuild. Values below are only the baked fallback.
ART_MIN_WIDTH = 600
FOOTPRINT_FALLBACK = {
    "max":     {"w": 860, "h": 532, "x": 1, "y": 0},
    "maya":    {"w": 860, "h": 532, "x": 1, "y": -36},
    "houdini": {"w": 1030, "h": 580, "x": 0, "y": 20},
}


def _load_footprint(dcc_key, splash_dir):
    """Per-DCC splash footprint: drive-side splash_config.json wins,
    baked fallback otherwise. Physical px; y negative = up."""
    import json
    import os
    fp = dict(FOOTPRINT_FALLBACK.get(dcc_key)
              or {"w": 860, "h": 532, "x": 0, "y": 0})
    fp.setdefault("x", 0)
    if splash_dir:
        cfg_path = os.path.join(splash_dir, "splash_config.json")
        try:
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    entry = json.load(f).get(dcc_key, {})
                for k in ("w", "h", "x", "y"):
                    if isinstance(entry.get(k), (int, float)):
                        fp[k] = entry[k]
        except Exception as e:
            log("splash_config.json unreadable: %s" % e)
    return fp

# substring expected in the DCC main window title, per DCC key
MARKER = {"max": "3ds Max", "maya": "Maya", "houdini": "Houdini"}


def _dcc_window_present(pid, marker):
    """True when the process has a visible, captioned top-level window whose
    title contains the marker — i.e. the real main window, not the native
    boot splash (splash windows are caption-less popups)."""
    try:
        user32 = ctypes.windll.user32
        WS_CAPTION = 0x00C00000
        GWL_STYLE = -16
        found = [False]

        EnumProc = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _cb(hwnd, _lparam):
            try:
                if not user32.IsWindowVisible(hwnd):
                    return True
                wpid = wintypes.DWORD(0)
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
                if wpid.value != pid:
                    return True
                style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
                if not (style & WS_CAPTION):
                    return True
                n = user32.GetWindowTextLengthW(hwnd)
                if n <= 0:
                    return True
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if marker.lower() in buf.value.lower():
                    found[0] = True
                    return False
            except Exception:
                pass
            return True

        user32.GetWindowLongPtrW.restype = ctypes.c_longlong
        user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        try:
            user32.EnumWindows(EnumProc(_cb), 0)
        except Exception:
            pass  # EnumWindows "fails" when the callback stops it early
        return found[0]
    except Exception:
        return False


class LaunchSplash(QWidget):
    def __init__(self, dcc_key, dcc_label, proc, logo_path, art_path=None,
                 splash_dir=None):
        super().__init__(None)
        self._fp = _load_footprint(dcc_key, splash_dir)
        self._proc = proc
        self._marker = MARKER.get(dcc_key, dcc_label)
        self._label = dcc_label
        self._elapsed = 0
        self._dead_ms = 0
        self._closing = False

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                            | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        frame = QFrame(self)
        frame.setObjectName("taosSplash")
        frame.setStyleSheet(
            "#taosSplash { background-color: #16181c; border: 1px solid #2e3138;"
            " border-radius: 12px; }"
            " QLabel { color: #d8dade; font-family: 'Segoe UI';"
            " background: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        # custom art from the drive wins; logo card is the fallback.
        # art displays 600px wide - author at 1200px for crisp high-DPI.
        art = QPixmap(art_path) if art_path else QPixmap()
        if not art.isNull():
            # pure-art mode: no frame, no text - the image IS the splash
            frame.setStyleSheet(
                "#taosSplash { background: transparent; border: none; }")
            lay = QVBoxLayout(frame)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)
            scr = QApplication.primaryScreen()
            scr_w = scr.availableGeometry().width() if scr else 1920
            dpr = max(scr.devicePixelRatio() if scr else 1.0, 1.0)
            # cover-fit: smallest width whose scaled art covers the splash
            # footprint in BOTH dimensions (art aspect may differ from splash)
            target_w = self._fp["w"] / dpr
            target_h = self._fp["h"] / dpr
            aspect = art.width() / float(max(art.height(), 1))
            disp_w = int(max(target_w, target_h * aspect))
            disp_w = max(ART_MIN_WIDTH, min(disp_w, int(scr_w * 0.85)))
            if art.width() > disp_w:
                art.setDevicePixelRatio(art.width() / float(disp_w))
            elif art.width() < disp_w:
                art = art.scaledToWidth(disp_w, Qt.SmoothTransformation)
            art_lbl = QLabel()
            art_lbl.setPixmap(art)
            art_lbl.setAlignment(Qt.AlignHCenter)
            lay.addWidget(art_lbl)

            self._msg = None  # no status text in art mode
            self.setFixedWidth(disp_w)
            self.adjustSize()
        else:
            lay = QVBoxLayout(frame)
            lay.setContentsMargins(48, 40, 48, 30)
            lay.setSpacing(12)

            pix = QPixmap(logo_path)
            if not pix.isNull():
                pix = pix.scaledToWidth(240, Qt.SmoothTransformation)
                logo = QLabel()
                logo.setPixmap(pix)
                logo.setAlignment(Qt.AlignHCenter)
                lay.addWidget(logo)
            else:
                t = QLabel("TAOS")
                t.setStyleSheet("font-size: 40px; font-weight: 600; color: #fff;")
                t.setAlignment(Qt.AlignHCenter)
                lay.addWidget(t)

            sub = QLabel("The Alchemy of the Storm")
            sub.setStyleSheet("font-size: 12px; color: #8a8f98; letter-spacing: 2px;")
            sub.setAlignment(Qt.AlignHCenter)
            lay.addWidget(sub)

            lay.addSpacing(6)
            self._msg = QLabel("Launching %s ..." % dcc_label)
            self._msg.setStyleSheet("font-size: 13px; color: #c6c9cf;")
            self._msg.setAlignment(Qt.AlignHCenter)
            lay.addWidget(self._msg)

            hint = QLabel("click to dismiss")
            hint.setStyleSheet("font-size: 10px; color: #56595f;")
            hint.setAlignment(Qt.AlignHCenter)
            lay.addWidget(hint)

            self.setFixedWidth(400)
            self.adjustSize()

        screen = QApplication.primaryScreen()
        if screen is not None:
            geo = screen.geometry()  # absolute middle - matches the DCC splash
            dpr = max(screen.devicePixelRatio(), 1.0)
            x_off = int(self._fp.get("x", 0) / dpr)
            y_off = int(self._fp["y"] / dpr)
            self.move(geo.center().x() - self.width() // 2 + x_off,
                      geo.center().y() - self.height() // 2 + y_off)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(POLL_MS)

        self.show()
        self.raise_()
        log("launch splash shown for %s (pid %s)" % (dcc_key, proc.pid))

    # ---------- lifecycle ----------

    def _tick(self):
        if self._closing:
            return
        self._elapsed += POLL_MS
        self.raise_()

        # DCC main window is up -> linger briefly, then leave
        if _dcc_window_present(self._proc.pid, self._marker):
            if self._msg is not None:
                self._msg.setText("%s is ready" % self._label)
            self._finish_in(HOLD_MS, "dcc window appeared")
            return

        # process died before a window showed (crash / license bail)
        if self._proc.poll() is not None:
            self._dead_ms += POLL_MS
            if self._dead_ms >= EARLY_EXIT_GRACE_MS:
                self._finish_in(0, "dcc process exited during boot")
                return

        if self._elapsed >= TIMEOUT_MS:
            self._finish_in(0, "timeout")

    def _finish_in(self, delay_ms, reason):
        if self._closing:
            return
        self._closing = True
        self._timer.stop()
        log("launch splash closing (%s)" % reason)
        if delay_ms <= 0:
            self.close()
        else:
            QTimer.singleShot(delay_ms, self.close)

    def mousePressEvent(self, _event):
        self._closing = True
        self._timer.stop()
        log("launch splash dismissed by click")
        self.close()
