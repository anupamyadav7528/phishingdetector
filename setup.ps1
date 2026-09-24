$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe scripts\generate_smoke_data.py

Write-Host "Setup complete. Activate with .\.venv\Scripts\Activate.ps1"
Write-Host "Run tests with .\.venv\Scripts\python.exe -m pytest"
