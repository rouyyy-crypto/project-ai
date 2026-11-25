"""Wedding Band Hybrid AI Booking Agent — Gradio UI Entry Point (app.py).

Routes:
-------
- `/`         Direct shareable Customer Chat link (WhatsApp-style RTL interface + quick-reply starters).
- `/manager`  Dedicated Band Manager CRM Dashboard (KPI cards, status filters, lead inspector, status actions).
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import gradio as gr

from logic.database import (
    STATUS_CANCELLED,
    STATUS_CLOSED,
    STATUS_READY,
    get_lead_by_id,
    get_lead_statistics,
    get_leads,
    init_db,
    save_lead,
    update_lead_status,
)
from logic.rules_engine import check_availability_and_rules

DATA_DIR = Path(__file__).resolve().parent / "data"

INITIAL_BOT_MESSAGE = (
    "שלום וברוכים הבאים! 🎶 אני העוזר הדיגיטלי של להקת האירועים שלנו.\n"
    "אפשר לכתוב לי כאן בחופשיות כמו בוואטסאפ, או להתחיל בלחיצה על אחת האפשרויות המהירות למטה "
    "כדי שנוכל לבדוק זמינות, לענות על שאלות טכניות/רפרטואר או להעריך טווח מחיר לאירוע שלכם."
)

QUICK_START_OPTIONS: list[tuple[str, str]] = [
    ("📅 בדיקת זמינות לתאריך", "היי, אתם פנויים ב-2027-07-15?"),
    ("💍 אירוע: חתונה", "מדובר בחתונה, נשמח לבדוק פרטים והצעה ראשונית."),
    ("🎉 בר/בת מצווה או אירוע חברה", "מדובר באירוע בר מצווה / אירוע חברה, מה האפשרויות?"),
    ("🔊 הגברה ומפרט טכני", "האם אתם עושים הגברה גם בכסא כלה וגם בחופה בנוסף לבמה המרכזית?"),
    ("🎵 שיר חופה מיוחד ורפרטואר", "האם אתם מכינים עיבודים מיוחדים לשיר כניסת כלה לחופה?"),
    ("🎻 הרכב מינימלי (5 נגנים)", "אנחנו מתעניינים בהרכב מינימלי (5 נגנים), מה כלול בו ומה טווח המחיר?"),
]

FILTER_CHOICES: list[tuple[str, str]] = [
    ("הכל", "הכל"),
    ("מוכנות (ממתינות לאישור)", STATUS_READY),
    ("סגורות", STATUS_CLOSED),
    ("מבוטלות", STATUS_CANCELLED),
]

APP_CSS = """
.gradio-container {
    direction: rtl;
    text-align: center;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container p,
.gradio-container label,
.gradio-container span[data-testid="block-info"],
.gradio-container .prose,
.gradio-container .markdown-text,
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    text-align: center !important;
}

.gradio-container .wrap,
.gradio-container .gr-form,
.gradio-container fieldset,
.gradio-container [role="radiogroup"] {
    justify-content: center !important;
    text-align: center !important;
}

/* WhatsApp-style Customer Chat */
.wa-shell {
    max-width: 780px;
    margin: 0 auto;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
    border: 1px solid #d9e2dc;
    background: #efeae2;
    text-align: center;
}

.wa-header {
    background: linear-gradient(135deg, #075e54, #128c7e);
    color: #ffffff;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 8px;
}

.wa-header-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0;
}

.wa-header-sub {
    font-size: 0.86rem;
    opacity: 0.92;
    margin-top: 2px;
}

.wa-online-pill {
    background: rgba(255, 255, 255, 0.18);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    white-space: nowrap;
}

.wa-chatbot {
    background: #efeae2 !important;
    border: none !important;
    text-align: center !important;
}

.wa-chatbot .message,
.wa-chatbot .message p,
.wa-chatbot .message li {
    text-align: center !important;
}

.wa-chatbot .message ul {
    list-style: none;
    padding: 0;
}

.wa-quick-strip {
    padding: 10px 12px 6px 12px;
    background: #f7f5f0;
    border-top: 1px solid #e3ded5;
    text-align: center;
}

.wa-quick-strip .gr-row {
    justify-content: center !important;
}

.wa-quick-btn button {
    border-radius: 999px !important;
    font-size: 0.84rem !important;
    padding: 6px 12px !important;
    background: #ffffff !important;
    border: 1px solid #cde0d8 !important;
    color: #075e54 !important;
    text-align: center !important;
}

.wa-quick-btn button:hover {
    background: #e7f6f1 !important;
    border-color: #128c7e !important;
}

.wa-input-bar {
    background: #f0f2f5;
    padding: 8px 12px 12px 12px;
    border-top: 1px solid #dde2e5;
    justify-content: center !important;
}

/* Manager Dashboard */
.mgr-page {
    direction: rtl !important;
}

.mgr-header {
    background: linear-gradient(135deg, #1e293b, #334155);
    color: #f8fafc;
    padding: 18px 22px;
    border-radius: 14px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 10px;
    margin-bottom: 12px;
}

.mgr-link-pill {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.22);
    padding: 6px 14px;
    border-radius: 10px;
    font-size: 0.86rem;
    color: #e2e8f0;
    text-align: center;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 12px;
    margin: 6px 0 14px 0;
    direction: rtl !important;
}

.kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 14px 18px;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    direction: rtl !important;
    text-align: right !important;
}

.kpi-label {
    font-size: 0.85rem;
    color: #64748b;
    margin-bottom: 6px;
    text-align: right !important;
}

.kpi-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: #0f172a;
    text-align: right !important;
}

.kpi-ready { border-left: 5px solid #f59e0b !important; }
.kpi-closed { border-left: 5px solid #10b981 !important; }
.kpi-cancelled { border-left: 5px solid #ef4444 !important; }
.kpi-total { border-left: 5px solid #3b82f6 !important; }
.kpi-rate { border-left: 5px solid #8b5cf6 !important; }

/* Filter & Refresh row aligned to LEFT */
.mgr-controls-row {
    direction: rtl !important;
    display: flex !important;
    justify-content: flex-end !important;
    align-items: center !important;
    gap: 12px !important;
}

.mgr-controls-row > .mgr-controls-spacer {
    flex: 1 1 auto !important;
    min-width: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}

.mgr-controls-row > .mgr-filter-radio {
    flex: 0 1 auto !important;
    width: auto !important;
    min-width: 0 !important;
}

.mgr-controls-row > .mgr-refresh-btn {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 140px !important;
}

.mgr-filter-radio,
.mgr-filter-radio label,
.mgr-filter-radio span,
.mgr-filter-radio fieldset,
.mgr-filter-radio [role="radiogroup"] {
    text-align: left !important;
    justify-content: flex-end !important;
}

/* Table: Title RIGHT, Search LEFT, Columns RTL */
.mgr-table,
.mgr-table .table-container,
.mgr-table .table-wrap,
.mgr-table .virtual-table-viewport,
.mgr-table .header-table,
.mgr-table .header-table tr,
.mgr-table .virtual-body,
.mgr-table .virtual-row {
    direction: rtl !important;
}

.mgr-table .header-row {
    direction: rtl !important;
    display: flex !important;
    flex-direction: row !important;
    justify-content: space-between !important;
    align-items: center !important;
}

.mgr-table .header-row .label {
    margin-right: 0 !important;
    margin-left: auto !important;
    flex: 0 1 auto !important;
    text-align: right !important;
}

.mgr-table .header-row .label p {
    text-align: right !important;
}

.mgr-table .header-row .toolbar {
    margin-right: auto !important;
    margin-left: 0 !important;
}

.mgr-table table,
.mgr-table th,
.mgr-table td,
.mgr-table .cell-wrap {
    text-align: center !important;
    justify-content: center !important;
}

/* Detail section: RTL layout, centered inner text, colored left border */
.mgr-detail-row {
    direction: rtl !important;
}

.detail-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #64748b !important;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    direction: rtl;
    text-align: center !important;
}

.quote-range-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 5px solid #2563eb !important;
    border-radius: 12px;
    padding: 14px 16px;
    direction: rtl;
    text-align: center !important;
}

.quote-exact-box {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-left: 5px solid #059669 !important;
    border-radius: 12px;
    padding: 14px 16px;
    direction: rtl;
    text-align: center !important;
}

.quote-exact-box ul {
    list-style: none;
    padding: 0;
    margin: 8px 0 0 0;
    line-height: 1.7;
    text-align: center !important;
}

.disq-box {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 5px solid #dc2626 !important;
    border-radius: 12px;
    padding: 14px 16px;
    direction: rtl;
    text-align: center !important;
}

.transcript-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 14px;
    max-height: 290px;
    overflow-y: auto;
    white-space: pre-wrap;
    line-height: 1.6;
    font-size: 0.92rem;
    direction: rtl;
    text-align: center !important;
}
"""


def _new_chat_state() -> dict[str, Any]:
    """Initialize per-session conversational state for the UI preview adapter."""
    return {
        "event_date": None,
        "location": None,
        "guests_count": None,
        "event_type": None,
        "musical_style": None,
        "band_size": None,
        "sound_required": True,
        "client_name": None,
        "client_phone": None,
        "last_quote": None,
        "is_valid": None,
        "disqualification_reason": None,
        "lead_saved": False,
    }


def _mock_calculate_quote(
    date: str,
    location: str,
    guests_count: int,
    musical_style: str,
    band_size: int,
    sound_required: bool,
) -> dict[str, Any]:
    """Fallback deterministic quote matching DESIGN.md Section 9 until logic/pricing_calc.py is ready."""
    base_musicians_cost = band_size * 2000
    normalized_loc = (location or "").strip().lower()
    travel_surcharge = 0 if any(k in normalized_loc for k in ("ירושלים", "jerusalem")) else 800
    sound_equipment_cost = 2200 if sound_required else 0
    seasonal_adjustment = 0
    total_exact_price = (
        base_musicians_cost + travel_surcharge + sound_equipment_cost + seasonal_adjustment
    )
    return {
        "customer_price_range": {
            "min_price": total_exact_price,
            "max_price": total_exact_price + 1500,
        },
        "manager_exact_breakdown": {
            "base_musicians_cost": base_musicians_cost,
            "travel_surcharge": travel_surcharge,
            "sound_equipment_cost": sound_equipment_cost,
            "seasonal_adjustment": seasonal_adjustment,
            "total_exact_price": total_exact_price,
        },
    }


def _compute_quote(
    date: str,
    location: str,
    guests_count: int,
    musical_style: str,
    band_size: int,
    sound_required: bool,
) -> dict[str, Any]:
    """Delegate to logic.pricing_calc when implemented, otherwise use DESIGN.md mock fallback."""
    try:
        from logic.pricing_calc import calculate_quote

        return calculate_quote(date, location, guests_count, musical_style, band_size, sound_required)
    except (ImportError, NotImplementedError):
        return _mock_calculate_quote(
            date, location, guests_count, musical_style, band_size, sound_required
        )


def _extract_state_updates(text: str, state: dict[str, Any]) -> bool:
    """Extract simple event parameters from Hebrew message; returns True if quote params changed."""
    changed = False

    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if date_match and state["event_date"] != date_match.group(1):
        state["event_date"] = date_match.group(1)
        changed = True

    guests_match = re.search(r"(\d{2,4})\s*(?:אורח|אורחים|מוזמנים)", text)
    if guests_match:
        new_guests = int(guests_match.group(1))
        if state["guests_count"] != new_guests:
            state["guests_count"] = new_guests
            changed = True

    for keyword, canonical in [
        ("חתונה", "חתונה"),
        ("מתחתנים", "חתונה"),
        ("בר מצווה", "בר מצווה"),
        ("בת מצווה", "בת מצווה"),
        ("אירוע חברה", "אירוע חברה"),
        ("אירוע פרטי", "אירוע פרטי"),
    ]:
        if keyword in text and state["event_type"] != canonical:
            state["event_type"] = canonical
            changed = True
            break

    for city in ("ירושלים", "תל אביב", "מודיעין", "רעננה", "פתח תקווה", "אשדוד", "חיפה", "חדרה", "נס ציונה"):
        if city in text and state["location"] != city:
            state["location"] = city
            changed = True
            break

    for style in ("ישראלי-חסידי", "חסידי", "ישראלי", "מזרחי", "כלייזמר", "ג'אז"):
        if style in text and state["musical_style"] != style:
            state["musical_style"] = style
            changed = True
            break

    if any(k in text for k in ("מינימלי", "5 נגנים", "חמישייה")):
        if state["band_size"] != 5:
            state["band_size"] = 5
            changed = True
    elif any(k in text for k in ("6 נגנים", "שישייה", "להוסיף נגן", "להוסיף גם כינור", "נגן סולו נוסף")) and state["band_size"] != 6:
        state["band_size"] = 6
        changed = True

    phone_match = re.search(r"(05\d[-\s]?\d{7})", text)
    if phone_match:
        state["client_phone"] = phone_match.group(1)

    name_match = re.search(r"(?:שמי|קוראים לי|אני)\s+([א-ת]{2,}(?:\s+[א-ת]{2,})?)", text)
    if name_match and not any(w in name_match.group(1) for w in ("מתעניינים", "רוצה", "שואל")):
        state["client_name"] = name_match.group(1).strip()

    return changed


def _build_conversation_summary(state: dict[str, Any]) -> str:
    """Create a concise Hebrew summary of extracted event parameters for the Manager Dashboard."""
    parts = [
        f"סוג אירוע: {state.get('event_type') or 'לא צוין'}",
        f"תאריך: {state.get('event_date') or 'לא צוין'}",
        f"מיקום/אולם: {state.get('location') or 'לא צוין'}",
        f"מספר אורחים: {state.get('guests_count') or 'לא צוין'}",
        f"סגנון מוזיקלי: {state.get('musical_style') or 'לא צוין'}",
        f"גודל הרכב: {state.get('band_size') or 'לא צוין'} נגנים",
    ]
    if state.get("disqualification_reason"):
        parts.append(f"סיבת סינון: {state['disqualification_reason']}")
    return " | ".join(parts)


def _kb_snippet_answer(text: str) -> list[str]:
    """Provide grounded snippets from local data/*.txt when user asks tech/repertoire questions."""
    answers: list[str] = []
    if any(k in text for k in ("הגברה", "סאונד", "כסא כלה", "חופה", "חשמל", "במה")):
        answers.append(
            "🔊 **הגברה ומפרט טכני:** הלהקה מספקת כיסוי סאונד מלא ל־3 מוקדי האירוע "
            "(עמדת כסא כלה, טקס החופה והבמה המרכזית), כולל טכנאי סאונד ייעודי שמביא את כל הציוד, מקים ומפעיל אותו."
        )
    if any(k in text for k in ("רפרטואר", "שיר", "עיבוד", "כניסת כלה", "סגנון")):
        answers.append(
            "🎵 **רפרטואר ושירים מיוחדים:** הלהקה מנגנת סגנונות יהודי/חסידי, ישראלי, מזרחי שורשי, כלייזמר וג'אז, "
            "ויכולה ללמוד עד **2 שירים חדשים** במיוחד עבור הזוג (כגון כניסת כלה לחופה) בהודעה של לפחות 30 יום מראש."
        )
    return answers


def _preview_agent_reply(
    user_message: str,
    history: list[dict[str, Any]],
    state: dict[str, Any],
) -> str:
    """UI Preview conversation adapter using real rules_engine + database + DESIGN.md mock pricing.

    Once `agents/orchestrator.py` is implemented by the AI module owner, this adapter
    can be replaced or bypassed by calling `agents.orchestrator` directly.
    """
    try:
        from agents.orchestrator import handle_message  # type: ignore[import-not-found]

        return handle_message(user_message, history, state)
    except ImportError:
        pass

    params_changed = _extract_state_updates(user_message, state)
    replies: list[str] = []

    # 1. Check availability & rules whenever a date is known and parameters changed
    if state["event_date"] and (params_changed or state["is_valid"] is None):
        rule_res = check_availability_and_rules(
            date=state["event_date"],
            location=state["location"],
            guests_count=state["guests_count"],
            event_type=state["event_type"],
        )
        state["is_valid"] = rule_res["is_valid"]
        state["disqualification_reason"] = rule_res["disqualification_reason"]

        if not rule_res["is_valid"]:
            reason = rule_res["disqualification_reason"] or "חריגה מתנאי הסף."
            state["last_quote"] = None
            if not state["lead_saved"]:
                save_lead(
                    client_name=state.get("client_name") or "זוג מתעניין (תצוגת צ'אט)",
                    lead_input={
                        "client_name": state.get("client_name") or "זוג מתעניין",
                        "client_phone": state.get("client_phone") or "",
                        "event_date": state.get("event_date") or "",
                        "city": state.get("location") or "",
                        "guests_count": state.get("guests_count"),
                        "event_type": state.get("event_type") or "",
                        "band_size": state.get("band_size"),
                        "musical_style": state.get("musical_style") or "",
                        "sound_required": state.get("sound_required", True),
                    },
                    status=STATUS_CANCELLED,
                    transcript=history + [{"role": "user", "content": user_message}],
                    backend_response={
                        "is_valid": False,
                        "disqualification_reason": reason,
                        "customer_price_range": None,
                        "manager_exact_breakdown": None,
                    },
                    conversation_summary=_build_conversation_summary(state),
                )
                state["lead_saved"] = True

            kb_notes = _kb_snippet_answer(user_message)
            msg = (
                f"בדקתי ביומן שלנו לגבי **{state['event_date']}** — לצערנו לא נוכל לקיים את האירוע ({reason}).\n"
                "אם יש לכם גמישות בתאריך או בפרטים, אשמח לבדוק תאריך חלופי!"
            )
            if kb_notes:
                msg += "\n\n" + "\n".join(kb_notes)
            return msg

    # 2. Grounded KB snippets
    replies.extend(_kb_snippet_answer(user_message))

    # 3. Date confirmed available but missing some mandatory details
    if state["event_date"] and state["is_valid"] and not replies:
        replies.append(f"📅 התאריך **{state['event_date']}** פנוי ביומן שלנו!")

    # 4. Confirmation to forward lead to band manager
    confirm_words = ("אשמח", "מאשר", "תשלח", "שיחזור אלינו", "לסגור", "להעביר למנהל", "מעולה, תודה")
    if any(w in user_message for w in confirm_words) and state.get("last_quote") and state.get("is_valid"):
        if not state["lead_saved"]:
            quote = state["last_quote"]
            save_lead(
                client_name=state.get("client_name") or "זוג מתעניין (תצוגת צ'אט)",
                lead_input={
                    "client_name": state.get("client_name") or "זוג מתעניין",
                    "client_phone": state.get("client_phone") or "",
                    "event_date": state.get("event_date") or "",
                    "city": state.get("location") or "",
                    "guests_count": state.get("guests_count"),
                    "event_type": state.get("event_type") or "חתונה",
                    "band_size": state.get("band_size") or 5,
                    "musical_style": state.get("musical_style") or "",
                    "sound_required": state.get("sound_required", True),
                },
                status=STATUS_READY,
                transcript=history + [{"role": "user", "content": user_message}],
                backend_response={
                    "is_valid": True,
                    "disqualification_reason": None,
                    **quote,
                },
                conversation_summary=_build_conversation_summary(state),
            )
            state["lead_saved"] = True
        return (
            "נהדר! ✅ העברתי את פרטי האירוע, סיכום השיחה והמפרט אל מנהל הלהקה.\n"
            "המנהל יעבור על הפרטים ויחזור אליכם בהקדם עם הצעה מסודרת וסופית."
        )

    # 5. If mandatory quote details exist, calculate and show range ONLY (never fixed final price)
    has_quote_params = bool(
        state["event_date"]
        and state["is_valid"]
        and state["location"]
        and state["guests_count"]
        and (state["band_size"] or "הרכב" in user_message or "מחיר" in user_message)
    )
    if has_quote_params:
        band_size = state["band_size"] or 5
        state["band_size"] = band_size
        quote = _compute_quote(
            date=state["event_date"],
            location=state["location"],
            guests_count=state["guests_count"],
            musical_style=state["musical_style"] or "ישראלי-חסידי",
            band_size=band_size,
            sound_required=state["sound_required"],
        )
        state["last_quote"] = quote
        state["lead_saved"] = False  # Allow re-saving if parameters updated mid-chat
        pr = quote["customer_price_range"]
        lineup_desc = (
            "הרכב מינימלי של 5 נגנים (זמר, תופים, קלידים, גיטרה + כלי סולו לבחירה: קלרינט/כינור/סקסופון)"
            if band_size == 5
            else f"הרכב של {band_size} נגנים"
        )
        replies.append(
            f"📋 **סיכום פרטים וטווח מחיר משוער:**\n"
            f"- **תאריך:** {state['event_date']} | **מיקום:** {state['location']} | **אורחים:** ~{state['guests_count']}\n"
            f"- **הרכב:** {lineup_desc}, כולל **טכנאי סאונד ומערכת הגברה מלאה**\n"
            f"- **טווח מחיר משוער ללקוח:** ₪{pr['min_price']:,.0f} – ₪{pr['max_price']:,.0f} *(הערכה ראשונית בלבד, לא מחיר סופי)*\n\n"
            "האם תרצו שאעביר את הפנייה למנהל הלהקה לחזרה ואישור סופי?"
        )
        return "\n\n".join(replies)

    # 6. Ask cleanly for missing mandatory parameters
    missing = []
    if not state["event_date"]:
        missing.append("תאריך האירוע (לדוגמה: 2027-07-15)")
    if not state["event_type"]:
        missing.append("סוג האירוע (חתונה / בר מצווה / אירוע חברה)")
    if not state["location"]:
        missing.append("מיקום / עיר")
    if not state["guests_count"]:
        missing.append("כמות אורחים משוערת")
    if not state["band_size"]:
        missing.append("גודל הרכב מועדף (למשל הרכב מינימלי של 5 נגנים או מורחב)")

    if missing:
        replies.append(
            "כדי שאוכל לבדוק זמינות ולהעריך עבורכם טווח מחיר, אשמח לדעת:\n• "
            + "\n• ".join(missing)
        )
    return "\n\n".join(replies)


def on_customer_send(
    user_message: str,
    history: list[dict[str, Any]],
    state: dict[str, Any],
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Handle sending a chat message from input box or quick-reply option button."""
    text = (user_message or "").strip()
    if not text:
        return "", history, state
    reply = _preview_agent_reply(text, history, state)
    updated_history = history + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": reply},
    ]
    return "", updated_history, state


def on_customer_reset() -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Reset the customer chat to its initial welcome greeting."""
    return "", [{"role": "assistant", "content": INITIAL_BOT_MESSAGE}], _new_chat_state()


def _format_currency(val: Any) -> str:
    if val is None or val == "":
        return "—"
    return f"₪{float(val):,.0f}"


def _build_kpi_html(stats: dict[str, Any]) -> str:
    """Render clean KPI statistic cards for the Manager Dashboard."""
    cards = [
        ("סה\"כ פניות מתועדות", stats["total"], "kpi-total"),
        ("מוכנות (ממתינות לאישור)", stats["ready"], "kpi-ready"),
        ("סגורות (עסקאות שנסגרו)", stats["closed"], "kpi-closed"),
        ("מבוטלות (סוננו / אילוצים)", stats["cancelled"], "kpi-cancelled"),
        ("שיעור סגירה", f"{stats['close_rate_pct']}%", "kpi-rate"),
    ]
    cards_html = "".join(
        f"""
        <div class="kpi-card {css_cls}">
            <div class="kpi-label">{html.escape(label)}</div>
            <div class="kpi-value">{html.escape(str(value))}</div>
        </div>
        """
        for label, value, css_cls in cards
    )
    return f'<div class="kpi-grid">{cards_html}</div>'


def _leads_to_table_rows(leads: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for lead in leads:
        if lead["status"] == STATUS_CANCELLED:
            range_str = "לא ניתנה (סונן)"
        elif lead.get("min_price") is not None and lead.get("max_price") is not None:
            range_str = f"₪{lead['min_price']:,.0f} – ₪{lead['max_price']:,.0f}"
        else:
            range_str = "—"

        rows.append(
            [
                lead["id_lead"],
                lead.get("client_name") or "—",
                lead.get("event_date") or "—",
                lead.get("event_type") or "—",
                lead.get("venue_name") or "—",
                lead.get("guests_count") or "—",
                range_str,
                _format_currency(lead.get("quoted_price")),
                lead.get("status") or "—",
            ]
        )
    return rows


def _render_lead_details(lead_id: int | None) -> tuple[str, str, str, str]:
    """Return HTML panels for (summary+transcript, customer range, manager exact breakdown, header)."""
    if not lead_id:
        empty = "<div class='detail-card'>בחרו שיחה מהטבלה או מהרשימה כדי לצפות בסיכום השיחה ובהצעות המחיר.</div>"
        return empty, empty, empty, "לא נבחרה שיחה"

    lead = get_lead_by_id(int(lead_id))
    if not lead:
        missing = "<div class='detail-card'>הפנייה המבוקשת לא נמצאה במסד הנתונים.</div>"
        return missing, missing, missing, "פנייה לא נמצאה"

    header = f"שיחה #{lead['id_lead']} — {lead.get('client_name') or 'לקוח'} ({lead.get('status')})"

    summary_text = lead.get("conversation_summary") or (
        f"סוג אירוע: {lead.get('event_type') or '—'} | "
        f"תאריך: {lead.get('event_date') or '—'} | "
        f"מיקום/אולם: {lead.get('venue_name') or '—'} | "
        f"כלים מבוקשים: {lead.get('requested_instruments') or '—'}"
    )
    disq_html = ""
    if lead.get("disqualification_reason"):
        disq_html = (
            f"<div class='disq-box' style='margin-top:8px;'>"
            f"<strong>סיבת סינון / ביטול:</strong> {html.escape(str(lead['disqualification_reason']))}"
            f"</div>"
        )

    transcript_raw = lead.get("chat_transcript") or "אין תמלול זמין."
    summary_and_transcript_html = f"""
    <div class="detail-card">
        <div><strong>לקוח:</strong> {html.escape(str(lead.get('client_name') or '—'))} &nbsp;|&nbsp;
             <strong>טלפון:</strong> {html.escape(str(lead.get('client_phone') or '—'))} &nbsp;|&nbsp;
             <strong>סטטוס:</strong> {html.escape(str(lead.get('status') or '—'))}</div>
        <div style="margin-top:8px;"><strong>סיכום השיחה:</strong> {html.escape(summary_text)}</div>
        {disq_html}
        <div style="margin-top:10px; font-weight:600;">תמלול השיחה:</div>
        <div class="transcript-box">{html.escape(str(transcript_raw))}</div>
    </div>
    """

    # Customer-facing quote (range only, never fixed final price)
    if lead.get("status") == STATUS_CANCELLED:
        customer_quote_html = """
        <div class="disq-box">
            <strong>הצעת מחיר ללקוח:</strong><br/>
            לא ניתנה הצעת מחיר — השיחה סוננה בשלב בדיקת הזמינות / תנאי הסף.
        </div>
        """
    elif lead.get("min_price") is not None and lead.get("max_price") is not None:
        customer_quote_html = f"""
        <div class="quote-range-box">
            <strong>הצעת מחיר שניתנה ללקוח (טווח משוער בלבד — ללא מחיר סופי):</strong><br/>
            <span style="font-size:1.3rem; font-weight:700; color:#1d4ed8;">
                ₪{lead['min_price']:,.0f} – ₪{lead['max_price']:,.0f}
            </span>
        </div>
        """
    else:
        customer_quote_html = """
        <div class="quote-range-box">
            <strong>הצעת מחיר שניתנה ללקוח:</strong><br/>
            טרם תועד טווח מחיר עבור שיחה זו.
        </div>
        """

    # Manager exact breakdown
    bd = lead.get("breakdown_dict") or {}
    if bd:
        manager_exact_html = f"""
        <div class="quote-exact-box">
            <strong>הצעת מחיר מדויקת למנהל (פירוט דטרמיניסטי):</strong>
            <ul>
                <li>עלות נגנים בסיסית: <strong>{_format_currency(bd.get('base_musicians_cost'))}</strong></li>
                <li>תוספת נסיעות: <strong>{_format_currency(bd.get('travel_surcharge'))}</strong></li>
                <li>הגברה וסאונדמן: <strong>{_format_currency(bd.get('sound_equipment_cost'))}</strong></li>
                <li>התאמת עונה: <strong>{_format_currency(bd.get('seasonal_adjustment'))}</strong></li>
            </ul>
            <div style="margin-top:8px; font-size:1.2rem; font-weight:700; color:#047857;">
                סה"כ מחיר מדויק למנהל: {_format_currency(bd.get('total_exact_price'))}
            </div>
        </div>
        """
    elif lead.get("quoted_price") is not None:
        manager_exact_html = f"""
        <div class="quote-exact-box">
            <strong>הצעת מחיר מדויקת למנהל:</strong><br/>
            <span style="font-size:1.25rem; font-weight:700; color:#047857;">
                {_format_currency(lead.get('quoted_price'))}
            </span>
            <div style="font-size:0.85rem; color:#475569; margin-top:4px;">
                (רשומה זו נשמרה ללא פירוט סעיפים מפורק)
            </div>
        </div>
        """
    else:
        manager_exact_html = """
        <div class="detail-card">
            <strong>הצעת מחיר מדויקת למנהל:</strong> לא חושבה (פנייה מסוננת/חסרה).
        </div>
        """

    return summary_and_transcript_html, customer_quote_html, manager_exact_html, header


def refresh_dashboard(
    status_filter: str,
    selected_lead_id: int | None = None,
) -> tuple[str, list[list[Any]], Any, str, str, str, str]:
    """Reload KPI cards, filtered table, selector dropdown, and detail panel."""
    stats = get_lead_statistics(include_in_progress=False)
    leads = get_leads(status_filter=status_filter, include_in_progress=False)
    kpi_html = _build_kpi_html(stats)
    rows = _leads_to_table_rows(leads)

    choices = [
        (f"#{lead['id_lead']} | {lead.get('client_name') or 'לקוח'} ({lead.get('event_date') or 'ללא תאריך'})", lead["id_lead"])
        for lead in leads
    ]
    valid_ids = {lead["id_lead"] for lead in leads}
    chosen_id = selected_lead_id if selected_lead_id in valid_ids else (leads[0]["id_lead"] if leads else None)

    summary_html, cust_html, mgr_html, detail_title = _render_lead_details(chosen_id)
    dropdown_update = gr.update(choices=choices, value=chosen_id)
    return kpi_html, rows, dropdown_update, detail_title, summary_html, cust_html, mgr_html


def on_table_select(evt: gr.SelectData, table_rows: list[list[Any]]) -> tuple[int | None, str, str, str, str]:
    """Handle clicking any row in the Manager leads table."""
    if not table_rows or evt.index is None:
        return None, "לא נבחרה שיחה", "", "", ""
    row_idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else int(evt.index)
    if row_idx < 0 or row_idx >= len(table_rows):
        return None, "לא נבחרה שיחה", "", "", ""
    lead_id = int(table_rows[row_idx][0])
    summary_html, cust_html, mgr_html, detail_title = _render_lead_details(lead_id)
    return lead_id, detail_title, summary_html, cust_html, mgr_html


def on_dropdown_select(lead_id: int | None) -> tuple[str, str, str, str]:
    """Handle selecting a lead from the dropdown."""
    summary_html, cust_html, mgr_html, detail_title = _render_lead_details(lead_id)
    return detail_title, summary_html, cust_html, mgr_html


def on_change_lead_status(
    lead_id: int | None,
    new_status: str,
    status_filter: str,
):
    """Persist manager decision (closed/cancelled/ready) and refresh dashboard."""
    if lead_id:
        update_lead_status(int(lead_id), new_status)
    return refresh_dashboard(status_filter, selected_lead_id=lead_id)


def create_app() -> gr.Blocks:
    """Construct the multi-route Gradio application (/ for customers, /manager for band manager)."""
    init_db()

    # Route 1: Direct Customer Chat Link (`/`)
    with gr.Blocks(title="צ'אט הזמנת להקה | ייעוץ והצעת מחיר") as demo:
        gr.Navbar(visible=False)
        session_state = gr.State(_new_chat_state)

        with gr.Column(elem_classes=["wa-shell"]):
            gr.HTML(
                """
                <div class="wa-header">
                    <div>
                        <div class="wa-header-title">🎶 להקת האירועים — נציג AI להזמנות</div>
                        <div class="wa-header-sub">בדיקת תאריכים, התאמת הרכב וטווח מחיר משוער</div>
                    </div>
                    <div class="wa-online-pill">● זמין עכשיו</div>
                </div>
                """
            )

            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": INITIAL_BOT_MESSAGE}],
                rtl=True,
                layout="bubble",
                height=470,
                show_label=False,
                elem_classes=["wa-chatbot"],
            )

            with gr.Column(elem_classes=["wa-quick-strip"]):
                gr.Markdown("**אפשרויות התחלה מהירות (או כתבו הודעה חופשית למטה):**")
                with gr.Row():
                    quick_buttons = []
                    for label, prompt_text in QUICK_START_OPTIONS:
                        btn = gr.Button(label, size="sm", elem_classes=["wa-quick-btn"])
                        quick_buttons.append((btn, prompt_text))

            with gr.Row(elem_classes=["wa-input-bar"]):
                msg_box = gr.Textbox(
                    placeholder="כתבו הודעה כאן... (למשל: אתם פנויים ב-2027-07-15?)",
                    show_label=False,
                    scale=8,
                    container=False,
                )
                send_btn = gr.Button("שלח ➤", variant="primary", scale=1, min_width=90)
                reset_btn = gr.Button("שיחה חדשה", variant="secondary", scale=1, min_width=105)

        send_btn.click(
            fn=on_customer_send,
            inputs=[msg_box, chatbot, session_state],
            outputs=[msg_box, chatbot, session_state],
        )
        msg_box.submit(
            fn=on_customer_send,
            inputs=[msg_box, chatbot, session_state],
            outputs=[msg_box, chatbot, session_state],
        )
        reset_btn.click(
            fn=on_customer_reset,
            inputs=[],
            outputs=[msg_box, chatbot, session_state],
        )
        for btn, prompt_text in quick_buttons:
            btn.click(
                fn=lambda history, state, q=prompt_text: on_customer_send(q, history, state),
                inputs=[chatbot, session_state],
                outputs=[msg_box, chatbot, session_state],
            )

    # Route 2: Band Manager CRM Dashboard (`/manager`) — hidden from customer navbar
    with demo.route("דאשבורד מנהל", "/manager", show_in_navbar=False):
        gr.Navbar(visible=False)

        with gr.Column(elem_classes=["mgr-page"]):
            gr.HTML(
                """
                <div class="mgr-header">
                    <div>
                        <h2 style="margin:0; font-size:1.35rem;">🎛️ לוח בקרה למנהל הלהקה (CRM)</h2>
                        <div style="font-size:0.88rem; opacity:0.85; margin-top:4px;">
                            מעקב אחר שיחות מוכנות לאישור, עסקאות סגורות ושיחות שסוננו — כולל פירוט תמחור מדויק למנהל
                        </div>
                    </div>
                    <div class="mgr-link-pill">
                        קישור ישיר ללקוחות: <a href="/" target="_blank" style="color:#93c5fd; font-weight:700;">/ (פתיחת צ'אט לקוח)</a>
                    </div>
                </div>
                """
            )

            kpi_html_box = gr.HTML()

            with gr.Row(elem_classes=["mgr-controls-row"]):
                gr.HTML("", elem_classes=["mgr-controls-spacer"])
                status_filter = gr.Radio(
                    choices=FILTER_CHOICES,
                    value="הכל",
                    label="סינון לפי סטטוס שיחה",
                    scale=0,
                    elem_classes=["mgr-filter-radio"],
                )
                refresh_btn = gr.Button(
                    "🔄 רענן נתונים",
                    variant="secondary",
                    scale=0,
                    elem_classes=["mgr-refresh-btn"],
                )

            leads_table = gr.Dataframe(
                headers=[
                    "מזהה",
                    "שם לקוח",
                    "תאריך אירוע",
                    "סוג אירוע",
                    "מיקום/אולם",
                    "אורחים",
                    "הצעה ללקוח (טווח)",
                    "מחיר מדויק (מנהל)",
                    "סטטוס",
                ],
                datatype=["number", "str", "str", "str", "str", "str", "str", "str", "str"],
                type="array",
                interactive=False,
                show_search="search",
                elem_classes=["mgr-table"],
                label="רשימת שיחות ולידים (לחצו על שורה לכניסה לפרטי השיחה)",
            )

            gr.Markdown("### 🔍 פרטי שיחה נבחרת")
            with gr.Row(elem_classes=["mgr-detail-row"]):
                lead_selector = gr.Dropdown(label="בחירת שיחה מהירה", choices=[], value=None, scale=2)
                selected_title = gr.Textbox(label="כותרת שיחה", interactive=False, scale=3)

            with gr.Row(elem_classes=["mgr-detail-row"]):
                with gr.Column(scale=3):
                    detail_summary_html = gr.HTML()
                with gr.Column(scale=2):
                    detail_customer_quote_html = gr.HTML()
                    detail_manager_exact_html = gr.HTML()
                    gr.Markdown("**עדכון סטטוס עסקה:**")
                    with gr.Row(elem_classes=["mgr-detail-row"]):
                        btn_close_deal = gr.Button("סמן כסגורה ✅", variant="primary")
                        btn_cancel_deal = gr.Button("סמן כמבוטלת ❌", variant="stop")
                        btn_ready_deal = gr.Button("החזר למוכנה ⏳", variant="secondary")

        dashboard_outputs = [
            kpi_html_box,
            leads_table,
            lead_selector,
            selected_title,
            detail_summary_html,
            detail_customer_quote_html,
            detail_manager_exact_html,
        ]

        demo.load(
            fn=lambda: refresh_dashboard("הכל"),
            inputs=[],
            outputs=dashboard_outputs,
        )
        refresh_btn.click(
            fn=refresh_dashboard,
            inputs=[status_filter, lead_selector],
            outputs=dashboard_outputs,
        )
        status_filter.change(
            fn=lambda flt: refresh_dashboard(flt, None),
            inputs=[status_filter],
            outputs=dashboard_outputs,
        )
        leads_table.select(
            fn=on_table_select,
            inputs=[leads_table],
            outputs=[
                lead_selector,
                selected_title,
                detail_summary_html,
                detail_customer_quote_html,
                detail_manager_exact_html,
            ],
        )
        lead_selector.change(
            fn=on_dropdown_select,
            inputs=[lead_selector],
            outputs=[
                selected_title,
                detail_summary_html,
                detail_customer_quote_html,
                detail_manager_exact_html,
            ],
        )
        for status_btn, target_status in (
            (btn_close_deal, STATUS_CLOSED),
            (btn_cancel_deal, STATUS_CANCELLED),
            (btn_ready_deal, STATUS_READY),
        ):
            status_btn.click(
                fn=lambda lid, flt, st=target_status: on_change_lead_status(lid, st, flt),
                inputs=[lead_selector, status_filter],
                outputs=dashboard_outputs,
            )

    return demo


if __name__ == "__main__":
    app = create_app()
    app.launch(css=APP_CSS, theme=gr.themes.Soft())
