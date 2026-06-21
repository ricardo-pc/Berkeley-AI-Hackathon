from __future__ import annotations

import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "backend" / "api"
ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1] / "backend" / "orchestrator"
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR_ROOT))
sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(REPO_ROOT))
