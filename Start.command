#!/bin/bash
set -e
cd "$(dirname "$0")"
trap 'echo "Launch stopped. The error is above."; read -r -p "Press Return to close."' ERR
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v brew >/dev/null; then
  echo "Install Homebrew from https://brew.sh first, then run Start.command again."
  read -r -p "Press Return to close."
  exit 1
fi
py="$(brew --prefix)/opt/python@3.11/bin/python3.11"
media="$(brew --prefix)/opt/ffmpeg-full/bin"
if [[ ! -x "$py" || ! -x "$media/ffmpeg" ]]; then
  echo "Installing Python 3.11 and FFmpeg with subtitle support..."
  brew install python@3.11 ffmpeg-full
fi
export PATH="$media:$PATH"
if [[ ! -x .venv/bin/python ]]; then "$py" -m venv .venv; fi
if ! cmp -s requirements.txt .venv/installed-requirements; then
  .venv/bin/python -m pip install -r requirements.txt
  cp requirements.txt .venv/installed-requirements
fi
if curl -fsS --max-time 1 http://127.0.0.1:8642/_stcore/health >/dev/null 2>&1; then
  open http://127.0.0.1:8642
  exit 0
fi
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
echo "Studio address: http://127.0.0.1:8642 — keep this window open."
( for i in {1..40}; do
    if curl -fsS http://127.0.0.1:8642/_stcore/health >/dev/null 2>&1; then open http://127.0.0.1:8642; break; fi
    sleep 1
  done ) &
exec .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8642 --server.headless true --server.maxUploadSize 512
