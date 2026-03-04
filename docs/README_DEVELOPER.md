# Sarah Follow-Up Agent - Developer Handoff 🤖

## 📝 VERSION HISTORY & AI DEV LOGS
*This section acts as the communication channel between the AI (Wonderbot/Sarah) and the Human Dev Team. Every change to the project will be logged here with the "What" and the "Why".*

### [V2.1] - 2026-03-04 - API Endpoint Correction & Vapi Integration Documentation
*   **What:** Fixed API endpoint in `sarah_db_client.py` from `/context/{customer_id}/update` to `/conversation/{context_id}/update`. Updated all callers (`app.py`, `main.py`, `cron_worker.py`) to pass `context_id` (UUID) instead of `customer_id` (integer). Created comprehensive Vapi troubleshooting docs (`voice-ai/VAPI_NO_RESULT_FIX.md`, `voice-ai/MAKE_COM_FLOW_FIX.md`) and updated `voice-ai/make-scenario/setup.md` with correct response format for Make.com webhooks.
*   **Why:** Senior dev confirmed the correct endpoint is `/conversation/` not `/context/` - using wrong endpoint was causing conversation updates to fail. Vapi "No result returned" error was caused by Make.com wrapping responses in HTTP envelope instead of returning clean JSON with `{"results": [...]}` structure.

### [V2.0] - 2026-03-04 - Dynamic LLM Follow-ups & CRM Extraction
*   **What:** Replaced hardcoded follow-up strings in `cron_worker.py` with LLM-generated texts via `generate_smart_followup()`. Created `followup_strategy.json` to control timing and AI instructions. Added name/email extraction to `app.py`'s AI prompt, which now pushes data to `PUT /customers/{id}` via `sarah_db_client.py`. Cleaned up repo by moving all `.md` docs to `docs/`.
*   **Why:** To make follow-ups context-aware (V2 Architecture) rather than generic, and to automatically enrich the CRM database as the AI learns user details during natural conversation. Moving docs to `docs/` improves repo maintainability.

### [V1.1] - 2026-03-03 - API Routing Bugfix
*   **What:** Updated all Python files to pass `context_id` instead of `customer_id` into the `update_conversation` API call.
*   **Why:** The backend API strictly requires the UUID `context_id` to update the `Conversations` table. Passing the integer `customer_id` was causing AWS API Gateway 400 Bad Request errors.

### [V1.0] - 2026-02-26 - Initial State Machine Hack
*   **What:** Built the first iteration of the follow-up worker using the `intent` column as a state machine (`WAITING_FOR_ANSWER` -> `FOLLOWUP_1` -> `NURTURE`).
*   **Why:** The database lacked native automation-state fields, so we repurposed the `intent` field to track where the lead was in the follow-up funnel.

---

## 🏗️ V2 Architecture (Current State)

We have moved from **Static Automation (V1)** to **Intelligent CRM Sync (V2)**.

1.  **Context-Aware Follow-ups:** `cron_worker.py` no longer sends dumb templates. It reads `followup_strategy.json` for *instructions* (e.g., "Send a casual bump"), reads the last 4 messages of the chat history, and asks OpenAI to draft a personalized SMS that perfectly matches the context.
2.  **Dynamic Strategy:** Timing (e.g., wait 30 minutes, then wait 24 hours) and AI instructions are fully decoupled from Python. They live in `followup_strategy.json` for easy editing.
3.  **Auto-Enrichment:** When the Twilio webhook (`app.py`) receives a message, the LLM prompt not only generates a reply and summary, but it explicitly extracts `extracted_name` and `extracted_email`. If found, the Python backend instantly calls `PUT /customers/{id}` to update the core database.

---

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- `pip`
- Valid Core API Key (`x-api-key`)
- Twilio Account SID/Auth Token
- OpenAI API Key

### 2. Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install requests python-dotenv twilio openai
```

### 3. Configuration (.env)
Create a `.env` file in this directory:
```ini
CORE_API_KEY=your_actual_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
AGENT_NAME=Sarah
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
```

### 4. Running the Automation
The system has two parts:

**A. Inbound Webhook (`app.py`)**
Handles incoming SMS replies, generates smart responses, extracts CRM data, and updates the database.
```bash
# Run with Flask/Gunicorn via Docker
docker-compose up -d --build
```

**B. Outbound Worker (`cron_worker.py`)**
Checks for unresponsive leads via `followup_strategy.json` rules and sends LLM-generated follow-ups. Designed to run via Cron.
```bash
# Cron setup (Every 5 mins)
*/5 * * * * /path/to/venv/bin/python /path/to/cron_worker.py >> /var/log/sarah_worker.log 2>&1
```

---

## ⚠️ Known Hacks & API Limitations (For Backend Devs)

### 1. API Endpoint Workaround for Conversations
**Issue:** The endpoint `GET /conversations?status=active` currently returns **403 Forbidden** with the provided API key.
**Workaround:** The worker (`cron_worker.py`) instead calls **`GET /customers`** (iterates all customers) and then fetches `GET /context/{id}` for each one individually.
**Fix Needed:** Grant correct permissions for `GET /conversations` to the API Key, then we can revert `cron_worker.py` to use the batch endpoint to save massive API overhead.

### 2. State Machine via `intent` Field
**Context:** The Core DB schema does NOT have native fields for `automation_status` or `followup_count`.
**The Hack:** We utilize the **`intent`** field in the conversation context to track the automation state (`WAITING_FOR_ANSWER` -> `FOLLOWUP_1` -> `NURTURE`).