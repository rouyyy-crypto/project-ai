# System Design & MVP Boundaries: Hybrid AI Booking Agent for Wedding Bands

> **CRITICAL DIRECTIVE FOR AI CODING ASSISTANTS:**
> This document defines the strict scope, architecture, file structure, and operational rules for our Minimum Viable Product (MVP). Do **not** introduce out-of-scope features, external live APIs (e.g., Google Calendar, Google Maps, WhatsApp), or multi-tenant SaaS abstractions. Maintain strict separation between **Generative AI (natural language & RAG)** and **Deterministic Python Logic (availability, disqualification rules, & pricing calculations)**.

---

## 1. Project Overview & Core Objective

The system is a hybrid AI pre-sales and booking agent tailored exclusively for **wedding and event bands**. It replaces static "Contact Us" forms with an interactive, text-based conversational interface.

* **Core Engineering Philosophy:** Combine **Generative AI** (for natural Hebrew conversation, entity extraction, and document-grounded Q&A) with **Deterministic Code** (for calendar availability checks, rule-based lead filtering, and exact mathematical pricing—eliminating LLM hallucinations).
* **Target Users:**
  1. **Engaged Couples / Event Planners:** Interact via the Customer Chat UI to inquire about the band, specify event needs, and receive an initial specification & price range.
  2. **Band Managers:** Interact via the Internal CRM Dashboard to review "cooked" (qualified) leads, view conversation transcripts, inspect exact cost breakdowns, and approve final quotes.

---

## 2. End-to-End User Flow & Functional Rules

1. **Multi-Turn Needs Discovery:** The agent conducts a friendly, focused conversation in Hebrew to extract mandatory event parameters:
   * Event Date (`date`)
   * Event Location / City / Venue (`location`)
   * Estimated Guest Count (`guests_count`)
   * Event Type / Nature (`event_type`)
   * Preferred Musical Style & Band Size (`musical_style`, `band_size`)
2. **Document-Grounded Q&A (RAG):** At any point during the conversation, the user may ask technical or artistic questions (repertoire, lineup options, sound/lighting requirements, electricity specs). The agent must answer **strictly** based on the band's local knowledge base documents—never inventing songs or capabilities.
3. **Deterministic Availability & Disqualification Check:** Once mandatory parameters are gathered, the AI invokes a deterministic Python tool (`check_availability_and_rules`) to check the local calendar database and evaluate threshold rules (e.g., geographic distance limits, supported event types, minimum budget/guests).
   * *Rule:* If the lead violates any threshold or the date is booked, the agent politely declines the lead and clearly explains the reason.
4. **Controlled Price Transparency (Human-in-the-Loop):**
   * **Customer View (Chat UI):** If the lead is valid, the agent presents a complete event specification summary alongside an **estimated price range** (for expectation setting and pre-qualification), and asks for user confirmation to forward the inquiry to the band manager. **The AI must NEVER commit to a final fixed price.**
   * **Band Manager View (CRM Dashboard):** Upon confirmation (or disqualification), the lead is saved to the relational database with its status, conversation transcript, and the **exact deterministic cost breakdown** (base musician fees, travel distance surcharge, sound equipment costs, seasonality) for final manual approval.

---

## 3. Strict MVP Boundaries (In-Scope vs. Out-of-Scope)

| Dimension | ✅ IN-SCOPE (MVP Boundaries) | ❌ OUT-OF-SCOPE (Post-MVP Roadmap - Do NOT Build) |
| :--- | :--- | :--- |
| **Domain & Tenancy** | Single-tenant architecture built exclusively for wedding/event bands. | Multi-tenant SaaS onboarding, dynamic business builders, or other industries (carpenters, photographers, etc.). |
| **Communication Channels** | Web-based text chat interface (Hebrew UI/prompts, English code). | WhatsApp Business API, Twilio, email automation, or social media integrations. |
| **Modalities** | Text input/output only. | Voice AI (Speech-to-Text / Text-to-Speech) or Vision AI (analyzing venue photos/videos). |
| **External Integrations** | Self-contained local files and local database. | Live Google Calendar API, Google Maps Distance Matrix API, DocuSign, or accounting/invoicing APIs. |
| **Pricing & Closing** | Rule-based deterministic pricing via JSON config; outputs a price range to customer and exact breakdown to manager. | Dynamic Yield Management (ML surge pricing), automated PDF contract generation, or autonomous final quote binding. |

---

## 4. Module Architecture & Tool Types Matrix

The codebase is divided into 3 decoupled modules to prevent merge conflicts and maintain clean separation of concerns. **Do not mix UI logic, LLM orchestration, and SQL queries in the same file.**

| Module & Directory | Core Responsibility | Required Tool Types / Mechanisms (Abstract) | Specific Responsibilities & Constraints |
| :--- | :--- | :--- | :--- |
| **1. AI & RAG Engine**<br>(`agents/`) | Conversational flow, entity extraction, knowledge retrieval, and tool invocation. | • **Conversational LLM:** For Hebrew NLU, persona adherence, and structured entity extraction.<br>• **Multi-Turn Memory Management:** State tracking across conversation turns.<br>• **Semantic Search / Vector Store (RAG):** Local embedding & retrieval over band knowledge docs.<br>• **Function / Tool Calling:** Structured interface to trigger deterministic backend functions. | • Must enforce strict grounding in `data/` documents.<br>• Must never calculate prices internally; must delegate to `logic/` tools. |
| **2. Business Logic & Data**<br>(`logic/`) | Deterministic rules evaluation, availability checking, pricing math, and persistence. | • **Relational Database Engine:** Lightweight local SQL storage for calendar dates, pricing tables, and leads.<br>• **Externalized Rules Configuration:** Declarative config file (JSON) for flexible threshold/disqualification rules.<br>• **Deterministic Calculation Engine:** Pure mathematical functions for travel, lineup, sound, and seasonal pricing. | • Must return structured, predictable outputs (e.g., pass/fail + reason, price range + exact breakdown).<br>• Must handle edge cases (e.g., mid-conversation date/guest updates). |
| **3. Frontend & Showcase**<br>(`app.py`) | User interfaces for both customer interaction and manager lead review. | • **Python Web UI Framework:** Rapid dual-tab interface.<br>• **Session State Management:** Preserving chat history per user session.<br>• **Tabular Data Viewer:** Displaying live database records (leads, statuses, cost breakdowns) in the manager tab. | • Must provide a Split/Tabbed view: Tab 1 = Customer Chat, Tab 2 = Band Manager CRM Dashboard.<br>• Must support zero-cost cloud deployment. |

---

## 5. Standard Repository Structure

All new files and refactoring must strictly adhere to this directory layout:

```text
wedding-band-ai-agent/
├── app.py                  # Entry point: Dual-tab UI (Customer Chat + Band Manager CRM Dashboard)
├── .env                    # API keys (Excluded from Git via .gitignore)
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation, architecture diagram, and business overview
│
├── design/
│   └── DESIGN.md           # This architectural boundary & guidelines document
│
├── agents/                 # Module 1: AI & RAG
│   ├── orchestrator.py     # Conversation management, System Prompt, and Tool Calling execution
│   └── rag_engine.py       # Document loading, chunking, and local vector search
│
├── logic/                  # Module 2: Deterministic Code & Data
│   ├── database.py         # Relational DB operations (calendar, pricing lookup, lead persistence)
│   ├── rules_engine.py     # Date availability check & threshold disqualification logic
│   ├── pricing_calc.py     # Deterministic price calculation (range for client, exact for manager)
│   └── rules_config.json   # Configurable disqualification thresholds and base pricing parameters
│
└── data/                   # Domain Knowledge Base for RAG
    ├── repertoire.txt      # Song lists and supported musical genres
    ├── tech_specs.txt      # Sound, lighting, stage, and power specifications
    └── faq.txt             # Common couple FAQs and operational policies
```

---

## 6. Inter-Module Data Contract (JSON Interface)

When the AI Agent (`agents/orchestrator.py`) finishes extracting mandatory details and calls the deterministic backend (`logic/rules_engine.py` & `logic/pricing_calc.py`), data must conform to this structure:

```json
{
  "lead_input": {
    "client_name": "string",
    "event_date": "YYYY-MM-DD",
    "city": "string",
    "guests_count": "integer",
    "event_type": "string",
    "band_size": "integer",
    "sound_required": "boolean",
    "musical_style": "string"
  },
  "backend_response": {
    "is_valid": "boolean",
    "disqualification_reason": "string | null",
    "customer_price_range": {
      "min_price": "number",
      "max_price": "number"
    },
    "manager_exact_breakdown": {
      "base_musicians_cost": "number",
      "travel_surcharge": "number",
      "sound_equipment_cost": "number",
      "seasonal_adjustment": "number",
      "total_exact_price": "number"
    }
  }
}
```
---

## 7. End-to-End & Edge-Case Scenarios (תרחישים)

### Scenario 1: Happy Path – Valid Lead & Quote Approval
1. **Inquiry:** Engaged couple opens the Customer Chat UI and asks about availability and musical styles for a wedding.
2. **RAG Q&A:** Couple asks technical or artistic questions (e.g., repertoire, lineup options, sound/lighting/power specs). The agent answers strictly from the band's local knowledge base documents.
3. **Entity Extraction:** Through multi-turn conversation in Hebrew, the agent collects mandatory parameters: `date`, `location`, `guests_count`, `event_type`, `musical_style`, and `band_size`.
4. **Deterministic Check & Pricing:** Once mandatory parameters are gathered, the agent calls `check_availability_and_rules` and the deterministic pricing logic. Both pass.
5. **Client Quote & Approval:** The agent shows a summary of the event specs and an estimated price range (without committing to a final fixed price) and asks for confirmation to send the lead to the band manager.
6. **Lead Persistence:** Upon confirmation, the lead is saved to the database with its status, transcript, and exact cost breakdown for the Band Manager CRM Dashboard.

### Scenario 2: Disqualification – Date Already Booked
1. Couple provides event details for a date that is already booked in the local calendar database.
2. `check_availability_and_rules` returns `is_valid: false` with a disqualification reason for the booked date.
3. Agent politely declines the date and explains why, without committing to a quote.

### Scenario 3: Disqualification – Rule / Threshold Violation
1. Couple submits parameters that violate configured rules (e.g., outside geographic distance limits, unsupported event type, or below minimum guests/budget).
2. `check_availability_and_rules` returns `is_valid: false` with the specific disqualification reason.
3. Agent politely explains the limitation and records the disqualified lead in the database.

### Scenario 4: Mid-Conversation Parameter Change (Edge Case)
1. Couple initially provides valid details (such as a date and guest count) and receives an initial price range.
2. Before confirming, the couple changes the date or updates `guests_count` mid-conversation.
3. Agent re-runs `check_availability_and_rules` and pricing calculation with the updated values before presenting any updated range.

### Scenario 5: Out-of-Scope / Hallucination Guardrail
1. Couple asks for a song/capability not in the band's knowledge base or asks for a fixed/discounted price directly.
2. Agent does not invent songs/capabilities and does not state a price without deterministic calculation.

---

## 8. Interface Definitions (הגדרות ממשקים)

These interfaces define the expected inputs and outputs for the deterministic functions called by the AI orchestration layer (`agents/`) and implemented in the backend/database layer (`logic/`).

### 8.1 Availability & Rules Check Interface
- **Function / Tool Name:** `check_availability_and_rules`
- **Purpose:** Checks whether the requested event date is available in the local database and evaluates threshold/eligibility rules.
- **Input Parameters:**
  - `date` (`string`, `YYYY-MM-DD`)
  - `location` (`string`)
  - `guests_count` (`integer`)
  - `event_type` (`string`)
- **Return Payload:**
  - `is_valid` (`boolean`)
  - `disqualification_reason` (`string | null`)

### 8.2 Deterministic Pricing Interface
- **Function / Tool Name:** `calculate_quote` (or deterministic pricing entry point in `logic/`)
- **Purpose:** Computes an estimated price range for the customer view and an exact cost breakdown for the band manager view based on deterministic rules and pricing data.
- **Input Parameters:**
  - `date` (`string`, `YYYY-MM-DD`)
  - `location` (`string`)
  - `guests_count` (`integer`)
  - `musical_style` (`string`)
  - `band_size` (`integer`)
  - `sound_required` (`boolean`)
- **Return Payload:**
  - `customer_price_range`: `{ "min_price": number, "max_price": number }`
  - `manager_exact_breakdown`: `{ "base_musicians_cost": number, "travel_surcharge": number, "sound_equipment_cost": number, "seasonal_adjustment": number, "total_exact_price": number }`

### 8.3 Lead Persistence Interface
- **Function / Tool Name:** `save_lead` (or database persistence function in `logic/`)
- **Purpose:** Saves qualified ("cooked") leads upon user confirmation—or disqualified leads when rejected by rules—along with status, conversation transcript, and pricing/disqualification details for the CRM dashboard.
- **Input Parameters:**
  - `client_name` (`string`)
  - `lead_input` (`object`, matching Section 6)
  - `status` (`string`, e.g., `"qualified"` / `"disqualified"`)
  - `transcript` (`string | list`)
  - `backend_response` (`object`, matching Section 6)
- **Return Payload:**
  - `saved` (`boolean`)
  - `lead_id` (`integer | string | null`)

  ---

## 9. Mock Functions (פונקציות דמה)

Placeholder implementations matching the Section 8 interfaces so agent and UI flows can be tested against predictable mock data before final backend/database logic is complete[cite: 2, 3, 4].

```python
from typing import Any, Dict, List, Optional


def check_availability_and_rules(
    date: str,
    location: str,
    guests_count: int,
    event_type: str,
) -> Dict[str, Any]:
    """Mock availability and threshold/rule check."""
    booked_dates = {"2027-05-20", "2027-06-10"}

    if date in booked_dates:
        return {
            "is_valid": False,
            "disqualification_reason": "Requested date is already booked.",
        }

    if guests_count < 100:
        return {
            "is_valid": False,
            "disqualification_reason": "Guest count is below minimum threshold.",
        }

    return {
        "is_valid": True,
        "disqualification_reason": None,
    }


def calculate_quote(
    date: str,
    location: str,
    guests_count: int,
    musical_style: str,
    band_size: int,
    sound_required: bool,
) -> Dict[str, Any]:
    """Mock deterministic pricing calculation returning a customer range and manager breakdown."""
    base_musicians_cost = band_size * 2000
    travel_surcharge = 0 if location.strip().lower() in {"jerusalem", "ירושלים"} else 800
    sound_equipment_cost = 2200 if sound_required else 0
    seasonal_adjustment = 0
    total_exact_price = (
        base_musicians_cost
        + travel_surcharge
        + sound_equipment_cost
        + seasonal_adjustment
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


def save_lead(
    client_name: str,
    lead_input: Dict[str, Any],
    status: str,
    transcript: str | List[Dict[str, str]],
    backend_response: Dict[str, Any],
) -> Dict[str, Optional[Any]]:
    """Mock lead persistence returning a dummy saved status and lead ID."""
    return {
        "saved": True,
        "lead_id": 101,
    }