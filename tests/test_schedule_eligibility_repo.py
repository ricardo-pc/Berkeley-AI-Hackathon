from __future__ import annotations

import pytest

from scheduling_eligibility.errors import MissingSupabaseConfigError
from scheduling_eligibility.repo import SupabaseScheduleEligibilityRepo


def test_missing_supabase_config_raises_a_stable_error(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setattr("scheduling_eligibility.repo.load_environment", lambda: None)

    with pytest.raises(MissingSupabaseConfigError) as exc_info:
        SupabaseScheduleEligibilityRepo()

    assert exc_info.value.code == "missing_supabase_config"
    assert exc_info.value.status_code == 500
