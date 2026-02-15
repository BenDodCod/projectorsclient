# Quick run script for development
# Activates venv and runs the application

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

Write-Host "Running Projector Control..." -ForegroundColor Green
python src\main.py
