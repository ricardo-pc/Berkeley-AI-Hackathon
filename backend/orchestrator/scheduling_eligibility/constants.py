from __future__ import annotations

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# Demo-only clinic holiday list. Replace with the real clinic calendar before production use.
HOLIDAYS: set[str] = {
    "2026-01-01",  # New Year's Day
    "2026-07-04",  # Independence Day
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas
}

# A patient is flagged for a manual call once they've made MORE than this many
# reschedule requests since their last completed visit (i.e. this many prior
# requests already happened before the current one).
CONSECUTIVE_RESCHEDULE_THRESHOLD = 2

# How far ahead to search for an alternative slot when the requested time conflicts.
ALTERNATIVE_SLOT_SEARCH_DAYS = 14
ALTERNATIVE_SLOT_STEP_MINUTES = 15
