@echo off
rem Lance la Rich Presence dans une console (Ctrl+C pour arreter).
rem Inutile en temps normal : le jeu la lance tout seul une fois le mod installe.
cd /d "%~dp0"
python --version >nul 2>nul
if errorlevel 1 (
    py -3 -m sotf_rpc %*
) else (
    python -m sotf_rpc %*
)
if errorlevel 1 pause
