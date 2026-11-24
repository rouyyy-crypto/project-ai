"""Rules Engine Module (logic/rules_engine.py).

Core Responsibility:
--------------------
Deterministic availability verification and business rule threshold evaluation.
This module strictly decouples business validation from Generative AI logic.

Functions:
----------
1. `check_availability_and_rules(date, location=None, guests_count=None, event_type=None)`
   - Checks if date is booked in the local SQLite database (`booked_dates` table).
   - Validates threshold constraints if optional parameters are provided.
   - Conforms to Section 8.1 of DESIGN.md and supports Scenario 1 (date-only check).
2. `check_date_availability(date)`
   - Lightweight helper returning True if available, False if already booked.
"""

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional


def _get_db_path(custom_path: Optional[str] = None) -> Path:
    """Resolve database path relative to project root or use custom path."""
    if custom_path:
        return Path(custom_path)
    # Default: band_data.db in project root (parent of logic/)
    root_db = Path(__file__).resolve().parent.parent / "band_data.db"
    if root_db.exists():
        return root_db
    # Fallback to current working directory
    return Path("band_data.db")


def _get_config_path() -> Path:
    """Resolve rules_config.json path."""
    return Path(__file__).resolve().parent / "rules_config.json"


def check_date_availability(date: str, db_path: Optional[str] = None) -> bool:
    """Check if a specific date (YYYY-MM-DD) is free in the database.

    Returns True if available, False if already booked.
    """
    resolved_db = _get_db_path(db_path)
    if not resolved_db.exists():
        # Fallback safe check if DB file is not yet initialized
        return True

    try:
        conn = sqlite3.connect(resolved_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM booked_dates WHERE event_date = ? LIMIT 1",
            (date.strip(),),
        )
        row = cursor.fetchone()
        conn.close()
        return row is None
    except sqlite3.Error:
        return True


def check_availability_and_rules(
    date: str,
    location: Optional[str] = None,
    guests_count: Optional[int] = None,
    event_type: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify calendar availability and threshold rules.

    Parameters
    ----------
    date : str
        Mandatory event date in YYYY-MM-DD format.
    location : Optional[str]
        Event venue or city (checked against distance/regional boundaries if provided).
    guests_count : Optional[int]
        Estimated number of guests (checked against min/max thresholds if provided).
    event_type : Optional[str]
        Nature of event (wedding, bar mitzvah, etc., checked against supported types).
    db_path : Optional[str]
        Optional custom path to SQLite database.

    Returns
    -------
    dict:
        {
            "is_valid": bool,
            "disqualification_reason": str | None
        }
    """
    # 1. Calendar availability check (Mandatory gate)
    if not check_date_availability(date, db_path=db_path):
        return {
            "is_valid": False,
            "disqualification_reason": "Requested date is already booked.",
        }

    # Load thresholds from config if available
    config_path = _get_config_path()
    thresholds = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                thresholds = data.get("thresholds", {})
        except (json.JSONDecodeError, OSError):
            thresholds = {}

    min_guests = thresholds.get("min_guests", 50)
    max_guests = thresholds.get("max_guests", 1500)
    supported_types = thresholds.get("supported_event_types", [])

    # 2. Guest count threshold check (if provided)
    if guests_count is not None:
        if guests_count < min_guests:
            return {
                "is_valid": False,
                "disqualification_reason": f"Guest count ({guests_count}) is below minimum threshold of {min_guests}.",
            }
        if guests_count > max_guests:
            return {
                "is_valid": False,
                "disqualification_reason": f"Guest count ({guests_count}) exceeds maximum supported threshold of {max_guests}.",
            }

    # 3. Event type verification (if provided)
    if event_type and supported_types:
        normalized_event = event_type.strip().lower()
        normalized_supported = [t.lower() for t in supported_types]
        if not any(t in normalized_event or normalized_event in t for t in normalized_supported):
            return {
                "is_valid": False,
                "disqualification_reason": f"Event type '{event_type}' is not supported.",
            }

    return {
        "is_valid": True,
        "disqualification_reason": None,
    }
