# Scenarios

This file tracks concrete, incremental end-to-end scenarios for the **Wedding Band Hybrid AI Booking Agent**, starting from the thinnest possible slice and gradually adding complexity.

Unlike the high-level MVP behavioral categories in `DESIGN.md`, each scenario here describes a specific concrete interaction with observable inputs and expected outputs that we verify manually first and can later turn into automated tests.

---

## 1. Check Date Availability (Thin Slice)

**User:** Engaged couple or event planner in the Customer Chat UI.  
**Trigger:** The user wants to know if the band is free on a specific date.  
**Steps:**
1. The user enters an event date in Hebrew.
2. The agent checks availability for that date and responds whether it is available or already booked.
3. (If booked) The agent states that the date is unavailable without committing to a quote.

**Outcome:** The user receives an immediate, accurate availability answer for the requested date.

| User Input (Hebrew) | Expected Outcome / Behavior |
| :--- | :--- |
| "היי, אתם פנויים ב-2027-05-20?" | Reports that `2027-05-20` is **already booked** (unavailable) and does not offer a quote. |
| "האם אתם פנויים ב-2027-07-15?" | Reports that `2027-07-15` is **available** for an initial inquiry. |

---

## 2. Date Availability + Sound / Tech Specs (RAG)

**User:** Engaged couple planning a wedding.  
**Trigger:** The user asks about date availability and technical/sound equipment requirements in the same interaction.  
**Steps:**
1. The user asks about a date and technical/sound specifications.
2. The agent checks date availability and retrieves sound/tech details strictly from `data/tech_specs.txt`.
3. If the date is available, the agent confirms availability and provides full relevant sound/tech details. If the date is booked, the agent states it is unavailable, offers to check alternative dates if flexible, and answers the specific sound question briefly without dumping full technical specs.

**Outcome:** The user gets a clear date status plus context-appropriate, knowledge-base-grounded sound details.

| User Input (Hebrew) | Expected Outcome / Behavior |
| :--- | :--- |
| "אתם פנויים ב-2027-07-15? והאם אתם עושים הגברה גם בכסא כלה וגם בחופה בנוסף לבמה המרכזית?" | Confirms `2027-07-15` availability and answers sound/PA/tech details strictly from `data/tech_specs.txt`. |
| "האם אתם פנויים ב-2027-05-20 והאם אתם מביאים הגברה גם לכסא כלה וגם לחופה?" | States that `2027-05-20` is booked, offers to check alternative dates if they are flexible, and briefly confirms professional sound setup across the three focal points (bridal chair, chuppah, and main stage) from `data/tech_specs.txt` without dumping full specs. |

---

## 3. Follow-Up: Custom Chuppah Song Request & Repertoire (RAG)

**User:** Engaged couple continuing the conversation after `2027-07-15` was confirmed available.  
**Trigger:** The user asks about a specific song for *knisat kallah* / *chuppah* that is not in the standard repertoire.  
**Steps:**
1. The agent retains the confirmed available date (`2027-07-15`) from conversation context without re-querying date availability.
2. The agent checks repertoire and custom arrangement policy strictly in `data/repertoire.txt` and `data/faq.txt`.
3. The agent states what is supported or requires special arrangement per the docs, without inventing promises or fixed prices.

**Outcome:** The user receives an honest, grounded response on custom *chuppah* song policy while keeping conversation continuity.

| User Input (Hebrew) | Expected Outcome / Behavior |
| :--- | :--- |
| "מעולה! תגיד, אנחנו ממש רוצים שיר מיוחד לכניסת כלה לחופה שלא מופיע ברפרטואר הרגיל שלכם, אתם מכינים עיבודים מיוחדים?" | Retains `2027-07-15` context and addresses custom *chuppah* song/arrangement policy strictly from `data/repertoire.txt` and `data/faq.txt`. |

---

## 4. Follow-Up: Budget Constraints & Minimal Band Quote (400 Guests)

**User:** Engaged couple continuing from the previous turns (`2027-07-15` already confirmed available).  
**Trigger:** The couple provides the remaining event parameters (`location`, `guests_count`, `event_type`, `musical_style`) and asks for the price of a minimal band due to budget constraints.  
**Steps:**
1. The agent combines the stored date (`2027-07-15`) with the newly provided parameters and runs `check_availability_and_rules` and `calculate_quote` for a minimal 5-piece band (`band_size = 5`) with full sound included.
2. The agent explains the minimal lineup composition: **5 musicians** (singer, drums, keyboards, guitar, plus one solo instrument of choice: clarinet, violin, or saxophone).
3. The agent clarifies that the quote includes a **sound technician who brings the PA/sound equipment and operates it**.
4. The agent summarizes the event details, presents the deterministic estimated price range (`min_price`–`max_price`, never a fixed final price), and asks for confirmation to forward to the band manager.

**Outcome:** The couple receives a clear breakdown of the 5-piece minimal lineup, included sound technician/PA coverage, and an estimated price range.

| User Input (Hebrew) | Expected Outcome / Behavior |
| :--- | :--- |
| "אנחנו מתחתנים בירושלים ויהיו לנו בערך 400 אורחים, בסגנון ישראלי-חסידי. בגלל מגבלות תקציב חשוב לנו שיהיה יפה ושמח אבל יחסית זול — מה המחיר להרכב מינימלי?" | `is_valid: true`; details the 5-musician minimal lineup (singer, drums, keyboards, guitar + choice of clarinet/violin/saxophone), notes that a sound technician with full PA equipment and operation is included, shows event summary + estimated price range (`min_price`–`max_price`), and asks to confirm forwarding. |

---

## 5. Follow-Up: Pricing Inquiry for Adding an Extra Solo Musician

**User:** Engaged couple continuing directly from Scenario 4 (considering the 5-piece base package with clarinet as the solo instrument).  
**Trigger:** The couple asks how much it would cost to add an extra solo musician (e.g., adding a violin on top of the clarinet).  
**Steps:**
1. The agent queries the official band pricing data/database (`musicians` table rates and `calculate_quote` for `band_size = 6`).
2. The agent states the exact incremental cost added by the extra solo musician (violin) on top of the basic 5-piece package, along with the updated estimated price range (`min_price`–`max_price`).
3. The agent asks whether they prefer to proceed with the 5-piece or 6-piece lineup and confirm forwarding to the band manager.

**Outcome:** The couple gets an accurate, data-grounded price delta for adding a second solo musician and an updated total estimated range.

| User Input (Hebrew) | Expected Outcome / Behavior |
| :--- | :--- |
| "הבנתי, מעולה. אם אנחנו הולכים על קלרינט בתוך החמישייה הבסיסית, כמה יעלה לנו להוסיף נגן סולו נוסף – נגיד להוסיף גם כינור?" | Retrieves official musician pricing data, states how much adding the extra solo musician (violin) adds to the basic package price, shows the updated estimated price range, and prompts for confirmation. |

---

## 6. Lead Confirmation & CRM Persistence + Mid-Turn Update

**User:** Engaged couple who either changes event details mid-conversation or confirms the quote.  
**Trigger:** The couple updates a parameter (such as `guests_count`) before confirming, and then confirms forwarding the lead.  
**Steps:**
1. When parameters change mid-conversation, the agent re-runs `check_availability_and_rules` and `calculate_quote` with the updated values and updates the range/validity.
2. Upon user confirmation of a valid lead, the agent saves the lead (`save_lead`) with status, transcript, and exact cost breakdown for the Band Manager CRM Dashboard.

**Outcome:** The CRM dashboard/database reflects the latest accurate state and exact cost breakdown without stale quotes or duplicate broken states.

| User Input (Hebrew) | Expected Outcome / Behavior |
| :--- | :--- |
| "רגע, בעצם נראה שנהיה 450 אורחים ולא 400, זה משנה את הטווח?" | Re-runs `check_availability_and_rules` and `calculate_quote` with `450` guests, updates the estimated price range in the summary, and re-prompts for confirmation. |
| "מעולה, תודה! נשמח שמנהל הלהקה יחזור אלינו." | Calls `save_lead` with the latest event parameters, conversation transcript, and exact cost breakdown, and confirms to the user that the lead was forwarded to the band manager. |