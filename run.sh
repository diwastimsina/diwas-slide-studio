#!/bin/bash
echo "Starting Ollama..."
ollama serve &>/dev/null &
sleep 2

echo "Launching AI Slide Generator..."
cd "$(dirname "$0")"
streamlit run app.py --server.port 8501 --server.headless false
