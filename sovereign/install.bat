@echo off
setlocal enabledelayedexpansion

echo Installing SOVEREIGN...
py --version || goto :error

if not exist .venv (
  py -m venv .venv || goto :error
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip || goto :error
pip install -r requirements.txt || goto :error

where ollama >nul 2>nul
if %errorlevel% neq 0 (
  echo Ollama not found. Installing with winget...
  winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements || goto :error
)

ollama pull mistral || goto :error

echo Setup complete.
echo Run voice mode: python main.py --voice
echo Run text mode: python main.py --text
exit /b 0

:error
echo Installation failed.
exit /b 1
