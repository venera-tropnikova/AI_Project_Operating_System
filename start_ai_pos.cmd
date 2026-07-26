@echo off
REM AI POS portable launcher (Windows)
REM Double-click this file or run it from any drive/folder after moving AI POS.
chcp 65001 >nul
setlocal EnableExtensions

REM When started without --run (typical double-click), reopen minimized.
if /I not "%~1"=="--run" (
  start "AI POS" /min cmd /c call "%~f0" --run
  exit /b 0
)

REM Root = folder of this script (portable; no fixed drive letters).
cd /d "%~dp0"
if errorlevel 1 (
  echo Не удалось перейти в папку AI POS.
  pause
  exit /b 1
)

if not exist "tools\local_bridge.py" (
  echo Не найден tools\local_bridge.py рядом с этим файлом.
  echo Убедитесь, что вы запускаете start_ai_pos.cmd из корня AI POS.
  pause
  exit /b 1
)

set "PYEXE="
where py >nul 2>&1 && set "PYEXE=py"
if not defined PYEXE (
  where python >nul 2>&1 && set "PYEXE=python"
)
if not defined PYEXE (
  echo Для запуска AI POS установите Python 3
  pause
  exit /b 1
)

REM Open browser after a short delay so Local Bridge can bind port 8080.
start "" cmd /c "timeout /t 1 /nobreak >nul & start http://127.0.0.1:8080/"

echo AI POS запускается...
echo Остановка: закройте это окно или нажмите Ctrl+C
echo.

if /I "%PYEXE%"=="py" (
  py -3 "tools\local_bridge.py" --host 127.0.0.1 --port 8080
) else (
  python "tools\local_bridge.py" --host 127.0.0.1 --port 8080
)
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo AI POS завершился с ошибкой %ERR%.
  pause
)
exit /b %ERR%
