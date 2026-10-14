@echo off
rem Installe RedLoader (si besoin) et le mod SotFRPC dans le dossier du jeu.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mod\install.ps1" %*
pause
