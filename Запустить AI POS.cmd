@echo off
setlocal
set "ROOT=%~dp0"
start "" wscript.exe "%ROOT%start_ai_pos_silent.vbs"
exit /b 0
