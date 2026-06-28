@echo off
title AI Agent Map Simulator API
echo ======================================================
echo Starting AI Agent Map Simulator Backend...
echo ======================================================
cd /d "%~dp0"
call venv\Scripts\activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
