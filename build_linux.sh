#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

echo "========================================"
echo "  PrivateMC - Linux Build (ohne PPA)"
echo "========================================"

for path in app.py requirements.txt templates static; do
    if [[ ! -e "$path" ]]; then
        echo "FEHLER: Benötigte Datei/Ordner fehlt: $path"
        exit 1
    fi
done

if ! command -v docker >/dev/null 2>&1; then
    echo "FEHLER: Docker ist nicht installiert oder nicht im PATH."
    echo "Bitte Docker installieren und dieses Skript danach erneut starten."
    exit 1
fi

PROJECT_DIR="$(pwd)"

# Python 3.12 auf Debian Bookworm. glibc 2.36 ist deutlich älter
# als Ubuntu 26.04, und Bookworm ist aktueller als Bullseye.
docker run --rm \
    --volume "$PROJECT_DIR:/src" \
    --workdir /src \
    python:3.12-slim-bookworm \
    bash -Eeuc '
        export DEBIAN_FRONTEND=noninteractive

        apt-get update
        apt-get install -y --no-install-recommends \
            build-essential \
            patchelf \
            libffi-dev \
            zlib1g-dev \
            libjpeg62-turbo-dev \
            tk-dev \
            tcl-dev
        rm -rf /var/lib/apt/lists/*

        python --version
        python -c "import tkinter; print(\"Tkinter verfügbar\")"

        python -m venv /tmp/privatemc-build-venv
        source /tmp/privatemc-build-venv/bin/activate

        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
        python -m pip install --upgrade pyinstaller
        python -m py_compile app.py

        rm -rf build dist PrivateMC.spec

        python -m PyInstaller \
            --noconfirm \
            --clean \
            --onefile \
            --name PrivateMC \
            --hidden-import tkinter \
            --hidden-import tkinter.ttk \
            --hidden-import tkinter.simpledialog \
            --hidden-import tkinter.messagebox \
            --collect-all pystray \
            --collect-all PIL \
            --add-data "templates:templates" \
            --add-data "static:static" \
            app.py

        test -s dist/PrivateMC
        chmod 755 dist/PrivateMC
    '

echo
echo "Build abgeschlossen."
echo "Datei: $(pwd)/dist/PrivateMC"
echo
echo "Gebaut auf Debian Bookworm mit glibc 2.36."
echo "Bitte auf den tatsächlich unterstützten Linux-Versionen testen."
