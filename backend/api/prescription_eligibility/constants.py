from __future__ import annotations

# Patients at or above this age get the longer (12-month) recent-visit window;
# younger patients need a visit within the shorter (6-month) window. Real
# clinics set this per-doctor — these are demo defaults.
LONGER_WINDOW_AGE_THRESHOLD = 65
SHORT_VISIT_WINDOW_MONTHS = 6
LONG_VISIT_WINDOW_MONTHS = 12

# An "upcoming visit" must be scheduled within this many days to count.
UPCOMING_VISIT_WINDOW_DAYS = 365

# Demo-only known drug-interaction pairs (mirrors the warning MyChart/
# eClinicalWorks would show). Not a real clinical reference — replace with a
# proper interaction database before any real use.
CONFLICTING_MEDICATIONS: dict[str, set[str]] = {
    "lisinopril": {"amlodipine"},
    "amlodipine": {"lisinopril"},
}
