@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   PrivateMC - Windows Build
echo ========================================
echo.

py -m pip install --upgrade pip
if errorlevel 1 goto :error
py -m pip install -r requirements.txt
if errorlevel 1 goto :error
py -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

py -m PyInstaller --noconfirm --clean --onefile --windowed --name PrivateMC --collect-all flask --collect-all pystray --collect-all PIL --hidden-import=tkinter --hidden-import=tkinter.simpledialog --hidden-import=tkinter.messagebox --add-data "templates;templates" --add-data "static;static" app.py
if errorlevel 1 goto :error

echo.
echo Fertig: %CD%\dist\PrivateMC.exe
echo Kopiere diese EXE auf den Windows-PC und starte sie.
echo Beim ersten Start werden Admin-Passwort und Minecraft-EULA abgefragt.
echo Danach wird PrivateMC bei der Anmeldung automatisch gestartet.
echo.
pause
exit /b 0

:error
echo.
echo FEHLER: Build fehlgeschlagen. Lies die Fehlermeldung oben.
pause
exit /b 1
