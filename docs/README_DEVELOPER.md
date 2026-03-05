# Sarah Follow-Up Agent - Developer Handoff 🤖

## 📝 VERSION HISTORY & AI DEV LOGS
*This section acts as the communication channel between the AI (Wonderbot/Sarah) and the Human Dev Team. Every change to the project will be logged here with the "What" and the "Why".*

### [V2.5] - 2026-03-05 - Externalized Configuration for Multi-Client Deployment
*   **What:** Removed hardcoded URLs. Added required env vars: `MAKE_WEBHOOK_URL` (calendar integration), `CORE_API_URL` (API base URL). Updated `.env.example`, `docker-compose.yml`, and Python files to use these variables.
*   **Why:** Multi-client deployment. Each client needs unique Make.com webhook and potentially different API endpoints. Zero code changes per deployment now.

### [V2.4] - 2026-03-05 - Vapi Call Logging via Make.com
*   **What:** Created comprehensive implementation guide for logging Vapi voice calls to Sarah's database via Make.com webhooks (`voice-ai/VAPI_CALL_LOGGING.md`). Implemented end-of-call workflow that mirrors SMS conversation tracking: logs full transcript (POST /log with `channel: "voice"`), uses OpenAI to analyze call and extract summary/sentiment/intent/customer info, updates conversation state (POST /conversation/{context_id}/update), and conditionally updates customer profile (PATCH /customer/{customer_id}). Created API templates (`voice-ai/api/vapi-log-call.json`, `voice-ai/api/vapi-update-conversation.json`) with Make.com configuration examples.
*   **Why:** Vapi voice calls need to be tracked in the CRM just like SMS conversations. The Make.com scenario listens for Vapi's `end-of-call-report` webhook, processes the transcript, and updates Sarah's database to maintain unified conversation history across voice and text channels. Intent logic ensures answered calls mark leads as ENGAGED/HOT_LEAD (stopping automation), while voicemails/no-answers keep current automation state (continuing follow-ups).

### [V2.3] - 2026-03-04 - Function Calling (Tool Use) for Availability & Booking
*   **What:** Replaced the blind V2.2 webhook POST trigger with native OpenAI Function Calling (`manage_appointment`). The AI now prompts the user for a preferred date/time, automatically queries the Make.com webhook with `action: "check_availability"`, parses the returned slots, and relays them to the user. Once the user confirms a time, the AI calls the function again with `action: "book_appointment"`.
*   **Why:** Make.com doesn't just receive leads; it checks calendar availability and returns it. The AI needed to be able to pause mid-generation, ask Make.com what times are open, and use that JSON response to craft the final SMS message to the user.

### [V2.2] - 2026-03-04 - Make.com Booking Webhook Integration
*   **What:** Upgraded the LLM data extractor in `app.py` to identify if a lead explicitly requests an appointment, demo, or callback. If true, the system dynamically fires a POST request to the Make.com Webhook (`https://hook.us2.make.com/...`). 
*   **Why:** To transition leads instantly from "chatting via SMS" into the actual booking flow (presumably syncing them to Calendly/GoHighLevel via the Make.com scenario).

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

## 🚀 OPS DEPLOYMENT NOTES (V2.5 Changes)

### **New Environment Variables Required:**

```bash
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod  # Optional (has default)
MAKE_WEBHOOK_URL=https://hook.us2.make.com/client_webhook_id                  # REQUIRED per client
```

### **Multi-Client Deployment:**
- `MAKE_WEBHOOK_URL` - **Must be unique per client** (their Make.com scenario)
- `TWILIO_*` - Client-specific credentials
- `CORE_API_KEY` - Client-specific if multi-tenant
- See `.env.example` for complete reference

⚠️ **App will log warning on startup if `MAKE_WEBHOOK_URL` is missing - calendar booking will fail.**

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

Copy `.env.example` to `.env` and configure. New required variables as of V2.5:
- `CORE_API_URL` - API base URL (optional, has default)
- `MAKE_WEBHOOK_URL` - Make.com calendar webhook (required per client)

### 4. Running the Automation
The system has two parts:

**A. Inbound Webhook (`app.py`)**
Handles incoming SMS, generates AI responses, extracts CRM data. Deploy via `docker-compose up -d --build`.

**B. Outbound Worker (`cron_worker.py`)**
Checks unresponsive leads, sends LLM-generated follow-ups per `followup_strategy.json` rules.

---

## ⚠️ Known Hacks & API Limitations (For Backend Devs)

### 1. API Endpoint Workaround for Conversations
**Issue:** The endpoint `GET /conversations?status=active` currently returns **403 Forbidden** with the provided API key.
**Workaround:** The worker (`cron_worker.py`) instead calls **`GET /customers`** (iterates all customers) and then fetches `GET /context/{id}` for each one individually.
**Fix Needed:** Grant correct permissions for `GET /conversations` to the API Key, then we can revert `cron_worker.py` to use the batch endpoint to save massive API overhead.

### 2. State Machine via `intent` Field
**Context:** The Core DB schema does NOT have native fields for `automation_status` or `followup_count`.
**The Hack:** We utilize the **`intent`** field in the conversation context to track the automation state (`WAITING_FOR_ANSWER` -> `FOLLOWUP_1` -> `NURTURE`).