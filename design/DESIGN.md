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