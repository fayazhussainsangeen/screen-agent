#!/bin/bash
set -e

echo "Installing SOVEREIGN..."
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if ! command -v ollama &> /dev/null; then
  echo "Ollama not found. Installing..."
  curl -fsSL https://ollama.ai/install.sh | sh
fi

ollama pull mistral

echo "Setup complete."
echo "Run voice mode: python main.py --voice"
echo "Run text mode: python main.py --text"
