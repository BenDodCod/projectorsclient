@echo off
REM Quick run script for development
REM Activates venv and runs the application

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Running Projector Control...
python src\main.py

pause
