#!/bin/bash
# Build TAOS Launcher as a native macOS application bundle.
# Run on macOS; PyInstaller does not cross-compile between operating systems.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: build_macos.sh must run on macOS."
    exit 1
fi

echo "[1/5] Creating build environment..."
if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

HOST_ARCH="$(uname -m)"
PYTHON_ARCH="$(python -c 'import platform; print(platform.machine())')"
if [[ "$HOST_ARCH" != "$PYTHON_ARCH" ]]; then
    echo "WARNING: Host is ${HOST_ARCH}, but Python is ${PYTHON_ARCH}."
    echo "         The bundle will use the Python architecture and may require Rosetta."
fi

echo "[2/5] Installing build dependencies..."
python -m pip install --quiet --upgrade PySide6 pyinstaller pillow

VERSION="$(python bump_version.py --print)"
if [[ -z "$VERSION" ]]; then
    echo "ERROR: Could not determine the launcher version."
    exit 1
fi

echo "[3/5] Building TAOS Launcher v${VERSION}..."
pyinstaller \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --name TAOS_Launcher \
    --icon icons/taos_launcher_logo.png \
    --osx-bundle-identifier com.taos.launcher \
    --add-data "icons:icons" \
    main.py

APP="dist/TAOS_Launcher.app"
STANDALONE="dist/TAOS_Launcher"
PLIST="$APP/Contents/Info.plist"
if [[ ! -d "$APP" || ! -f "$PLIST" ]]; then
    echo "ERROR: PyInstaller did not produce $APP."
    exit 1
fi

echo "[4/5] Stamping version and applying ad-hoc signature..."
set_plist_value() {
    local key="$1"
    local value="$2"
    /usr/libexec/PlistBuddy -c "Set :${key} ${value}" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :${key} string ${value}" "$PLIST"
}
set_plist_value CFBundleShortVersionString "$VERSION"
set_plist_value CFBundleVersion "$VERSION"

# Ad-hoc signing is suitable for internal testing. A broadly distributed
# release should instead use a Developer ID certificate and Apple notarization.
codesign --force --sign - "$APP"

echo "[5/5] Verifying application bundle..."
codesign --verify --deep --strict --verbose=2 "$APP"

# --onedir --windowed also emits a standalone Unix distribution beside the
# self-contained .app. It is redundant for macOS delivery, so remove it only
# after the application bundle has passed verification.
if [[ -d "$STANDALONE" ]]; then
    rm -rf -- "$STANDALONE"
fi

echo
echo "Done: $SCRIPT_DIR/$APP"
echo "Bundle architecture: $(lipo -archs "$APP/Contents/MacOS/TAOS_Launcher")"
echo "This is an ad-hoc signed internal build; notarize public releases."
