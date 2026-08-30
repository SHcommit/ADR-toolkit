import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent / "skills" / "adr-toolkit"
sys.path.insert(0, str(SKILL_ROOT))
