@echo off
rem Starter Moonstone. Spillfilen er bygget inn i moonstone.exe.
cd /d "%~dp0"
moonstone.exe %*
if errorlevel 1 pause
