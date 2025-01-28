@echo off
cls
call .\.venv\Scripts\activate

echo Cleaning up...
call .\.venv\Scripts\python clean.py

call .\.venv\Scripts\python app.py
pause
