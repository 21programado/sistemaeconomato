@echo off
REM ======================================================
REM Crea un acceso directo en el Escritorio para la app
REM Debe estar en la misma carpeta que equipos.py
REM ======================================================

REM Carpeta donde está este .bat (y el .py)
SET SCRIPT_DIR=%~dp0

REM Script a ejecutar
SET SCRIPT_FILE=equipos.py

REM ===Atencion: Ruta de pythonw.exe (ajustar si es otra instalación)===
SET PYTHONW=C:\Program Files\Python314\pythonw.exe

REM Nombre del acceso directo
SET SHORTCUT_NAME=ControlEquipos.lnk

REM Ruta completa del acceso directo en el escritorio
SET SHORTCUT=%USERPROFILE%\Desktop\%SHORTCUT_NAME%

REM Crear el acceso directo usando PowerShell
powershell -NoProfile -Command ^
"$ws = New-Object -ComObject WScript.Shell; ^
$desk = [Environment]::GetFolderPath('Desktop'); ^
$sc = $ws.CreateShortcut('%SHORTCUT%'); ^
$sc.TargetPath = '%PYTHONW%'; ^
$sc.Arguments = '\"%SCRIPT_DIR%%SCRIPT_FILE%\"'; ^
$sc.WorkingDirectory = '%SCRIPT_DIR%'; ^
$sc.IconLocation = '%PYTHONW%'; ^
$sc.Save();"

echo Acceso directo creado correctamente en el Escritorio.
pause
