"""Dark theme approximating the mockup."""

STYLESHEET = """
QMainWindow, QDialog, QMessageBox { background: #2e2e2e; }
QWidget { color: #b8b8b8; font-size: 12px; font-family: 'Segoe UI'; }

QLineEdit {
    background: #262626; border: 1px solid #3d3d3d; border-radius: 3px;
    padding: 5px 8px; color: #d8d8d8;
}
QLineEdit[locked="true"] { color: #6f6f6f; background: #2a2a2a; }
QLineEdit[invalid="true"] { border: 1px solid #a04040; }

QToolButton#lockBtn, QToolButton#resetBtn {
    background: transparent; border: none; font-size: 14px; padding: 2px;
}
QToolButton#lockBtn:hover, QToolButton#resetBtn:hover { color: #ffffff; }

QToolButton#dccBtn {
    background: transparent; border: none; border-radius: 8px; padding: 6px;
}
QToolButton#dccBtn:hover { background: #3a3a3a; }
QToolButton#dccBtn:pressed { background: #444444; }
QToolButton#dccBtn:disabled { background: transparent; }

QToolButton#settingsHeader {
    background: transparent; border: none; color: #9a9a9a;
    border-bottom: 1px solid #4a4a4a; padding: 4px 30px;
}
QToolButton#settingsHeader:hover { color: #d0d0d0; }

QLabel#statusStrip {
    color: #8a8a8a; padding: 4px 8px; border-top: 1px solid #3a3a3a;
}
QLabel#statusStrip[level="warn"] { color: #d0a050; }
QLabel#statusStrip[level="error"] { color: #c06060; }

QCheckBox { spacing: 8px; }
QPushButton {
    background: #3a3a3a; border: 1px solid #4a4a4a; border-radius: 3px;
    padding: 5px 14px; color: #c8c8c8;
}
QPushButton:hover { background: #454545; }
"""


def repolish(widget):
    """Re-apply dynamic property styling (locked/invalid states)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
