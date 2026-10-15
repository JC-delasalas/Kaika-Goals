#!/bin/zsh
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.lock"
  exit 1
fi
exec .venv/bin/python server.py --fixtures --port 8787
