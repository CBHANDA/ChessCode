#!/bin/sh
cd "$(dirname "$0")"
pip install -r requirements.txt --break-system-packages -q 2>/dev/null || pip install -r requirements.txt -q
python3 chess_gui.py
