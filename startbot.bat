cd /d "%~dp0"
if not exist ".venv" (
    python -m venv .venv
    .venv\Scripts\pip install -q -r requirements.txt
)
start "" .venv\Scripts\pythonw.exe main-craftfacts.py
exit
