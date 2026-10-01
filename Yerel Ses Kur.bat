@echo off
setlocal
title Nexus - Yerel Dogal Ses Kurulumu
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Once Nexus Baslat.bat dosyasini calistirin.
    pause
    exit /b 1
)

echo [1/2] Yerel ses motoru kuruluyor...
".venv\Scripts\python.exe" -m pip install -r requirements-tts.txt
if errorlevel 1 goto :error

echo [2/2] Supertonic Turkce modeli indiriliyor...
".venv\Scripts\python.exe" scripts\setup_local_tts.py --download
if errorlevel 1 goto :error

echo.
echo Yerel dogal ses hazir. .env icinde NEXUS_TTS_ENABLED=1 yapabilirsiniz.
pause
exit /b 0

:error
echo.
echo Kurulum tamamlanamadi. Yukaridaki hatayi inceleyin.
pause
exit /b 1
