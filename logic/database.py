"""Database & Lead Persistence Module (logic/database.py).

Core Responsibility:
--------------------
Relational SQLite schema initialization, safe additive migrations, and
deterministic read/write operations for leads, CRM dashboard views, and
calendar/pricing reference lookups.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Canonical UI / DB lead statuses
STATUS_READY = "ממתין לאישור"   # שיחות "מוכנות" - הסתיימו בהצעת מחיר ראשונית וממתינות למנהל
STATUS_CLOSED = "סגורה"          # שיחות "סגורות" - עסקה נסגרה סופית ע"י מנהל הלהקה
STATUS_CANCELLED = "מבוטלת"      # שיחות "מבוטלות" - סוננו עקב אילוצים (תאריך תפוס / חריגת סף)

# Future Extension Hook (disabled in MVP until team approves live session persistence)
STATUS_IN_PROGRESS = "בתהליך"   # שיחות מנוהלות (בתהליך) - שמור להרחבה עתידית
ENABLE_IN_PROGRESS_TRACKING = False

ACTIVE_DASHBOARD_STATUSES: tuple[str, ...] = (
    STATUS_READY,
    STATUS_CLOSED,
    STATUS_CANCELLED,
)

STATUS_ALIASES: dict[str, str] = {
    "qualified": STATUS_READY,
    "ready": STATUS_READY,
    "מוכנה": STATUS_READY,
    "מוכנות": STATUS_READY,
    "ממתין לאישור": STATUS_READY,
    "closed": STATUS_CLOSED,
    "סגורה": STATUS_CLOSED,
    "סגורות": STATUS_CLOSED,
    "disqualified": STATUS_CANCELLED,
    "cancelled": STATUS_CANCELLED,
    "מבוטלת": STATUS_CANCELLED,
    "מבוטלות": STATUS_CANCELLED,
    "in_progress": STATUS_IN_PROGRESS,
    "בתהליך": STATUS_IN_PROGRESS,
}


def get_db_path(custom_path: str | Path | None = None) -> Path:
    """Resolve SQLite database path relative to project root."""
    if custom_path:
        return Path(custom_path)
    root_db = Path(__file__).resolve().parent.parent / "band_data.db"
    if root_db.exists():
        return root_db
    return Path("band_data.db")


def normalize_status(status: str | None) -> str:
    """Normalize incoming status string (English/Hebrew) to canonical Hebrew status."""
    if not status:
        return STATUS_READY
    cleaned = status.strip()
    return STATUS_ALIASES.get(cleaned.lower(), STATUS_ALIASES.get(cleaned, cleaned))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _ensure_lead_columns(cursor: sqlite3.Cursor) -> None:
    """Safely add CRM detail columns to `leads` without breaking existing rows or seed_data.py."""
    cursor.execute("PRAGMA table_info(leads)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    migrations = {
        "min_price": "REAL",
        "max_price": "REAL",
        "price_breakdown": "TEXT",
        "conversation_summary": "TEXT",
        "disqualification_reason": "TEXT",
        "guests_count": "INTEGER",
        "musical_style": "TEXT",
        "band_size": "INTEGER",
        "sound_required": "INTEGER DEFAULT 1",
        "updated_at": "TEXT",
    }
    for col_name, col_type in migrations.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")


def init_db(db_path: str | Path | None = None) -> None:
    """Initialize all 4 core tables and run additive schema migrations."""
    resolved = get_db_path(db_path)
    conn = sqlite3.connect(resolved)
    cursor = conn.cursor()

    # 1. טבלת נגנים
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS musicians (
        id_musician INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        instrument TEXT NOT NULL,
        rate REAL NOT NULL,
        status TEXT,
        notes TEXT
    )
    """)

    # 2. טבלת אולמות
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venues (
        id_venue INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_name TEXT NOT NULL,
        address TEXT NOT NULL,
        distance_category INTEGER CHECK(distance_category IN (1, 2, 3)) NOT NULL,
        notes TEXT
    )
    """)

    # 3. יומן תאריכים תפוסים (לצורך סינון זמינות)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS booked_dates (
        id_booked INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """)

    # 4. טבלת לידים נכנסים (הלב של ה-MVP)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id_lead INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        client_phone TEXT,
        event_date TEXT,
        event_type TEXT,
        venue_name TEXT,
        requested_instruments TEXT,
        quoted_price REAL,
        chat_transcript TEXT,
        status TEXT DEFAULT 'ממתין לאישור',
        min_price REAL,
        max_price REAL,
        price_breakdown TEXT,
        conversation_summary TEXT,
        disqualification_reason TEXT,
        guests_count INTEGER,
        musical_style TEXT,
        band_size INTEGER,
        sound_required INTEGER DEFAULT 1,
        updated_at TEXT
    )
    """)

    _ensure_lead_columns(cursor)
    conn.commit()
    conn.close()


def _format_transcript(transcript: str | list[dict[str, Any]]) -> str:
    """Convert structured chat messages or plain text into readable UTF-8 transcript text."""
    if isinstance(transcript, str):
        return transcript
    lines: list[str] = []
    for msg in transcript:
        role = msg.get("role", "user")
        speaker = "לקוח" if role == "user" else "סוכן הלהקה"
        content = msg.get("content", "")
        if isinstance(content, list):
            parts = [str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in content]
            content = " ".join(parts)
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


def save_lead(
    client_name: str,
    lead_input: dict[str, Any],
    status: str,
    transcript: str | list[dict[str, Any]],
    backend_response: dict[str, Any],
    *,
    client_phone: str = "",
    requested_instruments: str = "",
    conversation_summary: str = "",
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Persist a qualified or disqualified lead per Section 8.3 of DESIGN.md."""
    init_db(db_path)
    resolved = get_db_path(db_path)
    canonical_status = normalize_status(status)

    price_range = backend_response.get("customer_price_range") or {}
    breakdown = backend_response.get("manager_exact_breakdown") or {}
    min_price = price_range.get("min_price")
    max_price = price_range.get("max_price")
    exact_total = breakdown.get("total_exact_price")
    disqualification_reason = backend_response.get("disqualification_reason")

    transcript_text = _format_transcript(transcript)
    breakdown_json = json.dumps(breakdown, ensure_ascii=False) if breakdown else None
    now_iso = _utc_now_iso()

    conn = sqlite3.connect(resolved)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO leads (
            client_name, client_phone, event_date, event_type, venue_name,
            requested_instruments, quoted_price, chat_transcript, status,
            min_price, max_price, price_breakdown, conversation_summary,
            disqualification_reason, guests_count, musical_style, band_size,
            sound_required, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            client_name or lead_input.get("client_name") or "לקוח ללא שם",
            client_phone or lead_input.get("client_phone") or "",
            lead_input.get("event_date") or "",
            lead_input.get("event_type") or "",
            lead_input.get("city") or lead_input.get("venue_name") or "",
            requested_instruments or lead_input.get("requested_instruments") or "",
            exact_total,
            transcript_text,
            canonical_status,
            min_price,
            max_price,
            breakdown_json,
            conversation_summary or "",
            disqualification_reason,
            lead_input.get("guests_count"),
            lead_input.get("musical_style") or "",
            lead_input.get("band_size"),
            1 if lead_input.get("sound_required", True) else 0,
            now_iso,
        ),
    )
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"saved": True, "lead_id": lead_id}


def _row_to_lead_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite Row from `leads` into a rich UI-ready dictionary."""
    data = dict(row)
    data["status"] = normalize_status(data.get("status"))

    raw_breakdown = data.get("price_breakdown")
    breakdown: dict[str, Any] = {}
    if raw_breakdown:
        try:
            breakdown = json.loads(raw_breakdown)
        except json.JSONDecodeError:
            breakdown = {}
    data["breakdown_dict"] = breakdown

    # Backwards-compatible fallback for rows inserted by seed_data.py without min/max/breakdown
    quoted = data.get("quoted_price")
    if data.get("min_price") is None and quoted is not None and data["status"] != STATUS_CANCELLED:
        data["min_price"] = float(quoted)
        data["max_price"] = round(float(quoted) * 1.15, 0)

    return data


def get_leads(
    status_filter: str | None = None,
    *,
    include_in_progress: bool = False,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Fetch leads for the Manager CRM Dashboard ordered newest first."""
    init_db(db_path)
    resolved = get_db_path(db_path)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    allowed_statuses = list(ACTIVE_DASHBOARD_STATUSES)
    if include_in_progress and ENABLE_IN_PROGRESS_TRACKING:
        allowed_statuses.append(STATUS_IN_PROGRESS)

    if status_filter and status_filter not in ("הכל", "all", "ALL"):
        canonical = normalize_status(status_filter)
        if canonical == STATUS_IN_PROGRESS and not (include_in_progress and ENABLE_IN_PROGRESS_TRACKING):
            conn.close()
            return []
        cursor.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY id_lead DESC",
            (canonical,),
        )
    else:
        placeholders = ",".join("?" for _ in allowed_statuses)
        cursor.execute(
            f"SELECT * FROM leads WHERE status IN ({placeholders}) ORDER BY id_lead DESC",
            tuple(allowed_statuses),
        )

    rows = cursor.fetchall()
    conn.close()
    return [_row_to_lead_dict(r) for r in rows]


def get_lead_by_id(lead_id: int, db_path: str | Path | None = None) -> dict[str, Any] | None:
    """Fetch a single lead record with parsed pricing breakdown."""
    init_db(db_path)
    resolved = get_db_path(db_path)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id_lead = ?", (int(lead_id),))
    row = cursor.fetchone()
    conn.close()
    return _row_to_lead_dict(row) if row else None


def update_lead_status(
    lead_id: int,
    new_status: str,
    db_path: str | Path | None = None,
) -> bool:
    """Update lead status from the Manager Dashboard (e.g., close or cancel)."""
    init_db(db_path)
    resolved = get_db_path(db_path)
    canonical = normalize_status(new_status)
    conn = sqlite3.connect(resolved)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET status = ?, updated_at = ? WHERE id_lead = ?",
        (canonical, _utc_now_iso(), int(lead_id)),
    )
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_lead_statistics(
    *,
    include_in_progress: bool = False,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return simple status counts and conversion rate for Dashboard KPI cards."""
    leads = get_leads(include_in_progress=include_in_progress, db_path=db_path)
    counts = {
        "total": len(leads),
        "ready": sum(1 for lead in leads if lead["status"] == STATUS_READY),
        "closed": sum(1 for lead in leads if lead["status"] == STATUS_CLOSED),
        "cancelled": sum(1 for lead in leads if lead["status"] == STATUS_CANCELLED),
        "in_progress": sum(1 for lead in leads if lead["status"] == STATUS_IN_PROGRESS),
    }
    decided = counts["closed"] + counts["cancelled"] + counts["ready"]
    counts["close_rate_pct"] = round((counts["closed"] / decided) * 100, 1) if decided else 0.0
    return counts


def upsert_active_conversation_stub(session_id: str, state: dict[str, Any]) -> None:
    """Future extension hook for tracking live 'בתהליך' conversations.

    Currently a no-op until team approves persisting live in-progress sessions.
    """
    if not ENABLE_IN_PROGRESS_TRACKING:
        return
    raise NotImplementedError("In-progress conversation persistence is pending team approval.")


if __name__ == "__main__":
    init_db()
    print("כל 4 הטבלאות (נגנים, אולמות, יומן תפוס ולידים) אותחלו בהצלחה!")
