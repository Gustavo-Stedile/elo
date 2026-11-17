from pathlib import Path
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
if os.name == "nt":
    VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON = ROOT / ".venv" / "bin" / "python"

python = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable

subprocess.run(
    [python, "-m", "uvicorn", "main:app", "--reload"],
    cwd=ROOT,
    check=True,
)
