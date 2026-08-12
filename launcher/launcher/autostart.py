"""Opt-in 'Start with Windows' via HKCU Run key. Never set without user consent."""
import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "TAOSLauncher"


def _exe_command():
    if getattr(sys, "frozen", False):
        return '"%s" --tray' % sys.executable
    return '"%s" "%s" --tray' % (sys.executable, sys.argv[0])


def set_autostart(enabled):
    if os.name != "nt":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, _exe_command())
            else:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
