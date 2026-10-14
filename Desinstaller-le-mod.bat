@echo off
rem Retire le mod SotFRPC du jeu, et RedLoader si aucun autre mod ne l'utilise.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mod\install.ps1" -Uninstall -RemoveRedLoader %*
pause
