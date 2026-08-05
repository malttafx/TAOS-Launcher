"""LockField: line edit + padlock toggle (+ optional reset-to-default).

Behavior (per Delcio's design):
  locked   = grey, read-only
  unlocked = white, editable
  locking  = validate -> if invalid, warn + explain, user chooses to
             save anyway or keep editing -> save to disk on lock
"""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit,
                               QToolButton, QMessageBox)

from .theme import repolish

LOCK_GLYPH = "\U0001F512"      # closed padlock
UNLOCK_GLYPH = "\U0001F513"    # open padlock
RESET_GLYPH = "↺"         # anticlockwise arrow


class LockField(QWidget):
    lockCommitted = Signal(str)   # emitted with the text after a lock is accepted
    resetRequested = Signal()

    def __init__(self, label, placeholder="", locked=False, with_reset=False,
                 validator=None, label_width=70, parent=None):
        """validator: callable(text) -> None if ok, else problem description."""
        super().__init__(parent)
        self._validator = validator

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._label = QLabel(label)
        self._label.setFixedWidth(label_width)
        lay.addWidget(self._label)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        lay.addWidget(self.edit, 1)

        if with_reset:
            self._reset = QToolButton()
            self._reset.setObjectName("resetBtn")
            self._reset.setText(RESET_GLYPH)
            self._reset.setToolTip("Reset to team default")
            self._reset.setCursor(Qt.PointingHandCursor)
            self._reset.clicked.connect(self.resetRequested.emit)
            lay.addWidget(self._reset)

        self._lock = QToolButton()
        self._lock.setObjectName("lockBtn")
        self._lock.setCursor(Qt.PointingHandCursor)
        self._lock.clicked.connect(self._on_lock_clicked)
        lay.addWidget(self._lock)

        self._apply_locked(locked)

    # ---------- public ----------

    def text(self):
        return self.edit.text().strip()

    def setText(self, text):
        self.edit.setText(text)

    def is_locked(self):
        return self._locked

    def set_locked(self, locked):
        self._apply_locked(locked)

    def mark_invalid(self, invalid):
        self.edit.setProperty("invalid", "true" if invalid else "false")
        repolish(self.edit)

    # ---------- internals ----------

    def _apply_locked(self, locked):
        self._locked = locked
        self.edit.setReadOnly(locked)
        self.edit.setProperty("locked", "true" if locked else "false")
        repolish(self.edit)
        self._lock.setText(LOCK_GLYPH if locked else UNLOCK_GLYPH)
        self._lock.setToolTip("Unlock to edit" if locked else "Lock to save")

    def _on_lock_clicked(self):
        if self._locked:
            self._apply_locked(False)
            self.edit.setFocus()
            return

        # locking: validate first — warn + explain, never force
        text = self.text()
        problem = self._validator(text) if self._validator else None
        if problem:
            box = QMessageBox(self)
            box.setWindowTitle("Path problem")
            box.setIcon(QMessageBox.Warning)
            box.setText(problem)
            box.setInformativeText("You can save it anyway and fix it later.")
            save = box.addButton("Save anyway", QMessageBox.AcceptRole)
            box.addButton("Keep editing", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() is not save:
                return  # stay unlocked
            self.mark_invalid(True)
        else:
            self.mark_invalid(False)

        self._apply_locked(True)
        self.lockCommitted.emit(text)
