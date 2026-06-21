from __future__ import annotations

import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "backend" / "api"
ELIGIBILITY_SERVICE_ROOT = Path(__file__).resolve().parents[1] / "backend" / "eligibility_service"
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ELIGIBILITY_SERVICE_ROOT))
sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(REPO_ROOT))
