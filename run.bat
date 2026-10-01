@echo off
cd /d "%~dp0"
pip install -r requirements.txt
python chess_gui.py
pause
