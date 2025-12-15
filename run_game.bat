@echo off
REM Adaptif AI Nişan Alma Oyunu Başlatıcısı
echo Oyun baslatiliyor...

cd /d "%~dp0"
.venv\Scripts\python.exe main.py

pause
