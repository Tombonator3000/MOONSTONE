@echo off
rem Starter Moonstone. Spillfilen ligger i mappen "spill" (Moonstonecd32-AMIGA.zip).
cd /d "%~dp0"
moonstone.exe %*
if errorlevel 1 pause
