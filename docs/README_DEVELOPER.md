# Sarah Follow-Up Agent - Developer Handoff 🤖

## 📝 VERSION HISTORY & AI DEV LOGS
*This section acts as the communication channel between the AI (Wonderbot/Sarah) and the Human Dev Team. Every change to the project will be logged here with the "What" and the "Why".*

### [V2.6] - 2026-03-05 - DISCOVER -> QUALIFY -> ESCALATE & gpt-5.2 Migration
*   **What:** 
    1. Upgraded OpenAI model from `gpt-4o` to `gpt-5.2` (and updated function calling API from `function_call` to `tool_calls` parameter format).
    2. Overhauled the system prompt in `app.py` to use a "DISCOVER -> QUALIFY -> ESCALATE" conversational framework.
    3. Sarah now dynamically assigns an `interest_level` ("hot", "warm", "cold") to the lead, logs their `product_interest` (Receptionist, Sales, Chatbot, Custom), and flags `call_recommended`.
    4. Proactively offers phone calls if the lead signals they are "HOT".
*   **Why:** Sarah was previously too passive in her responses. The new prompt structure ensures she takes charge of the qualification process to identify serious buyers, categorize their needs into 4 specific product buckets, and proactively escalate to human/voice calls to close the deal faster. Model `gpt-5.2` provides the advanced reasoning required for this framework.

### [V2.5] - 2026-03-05 - Externalized Configuration for Multi-Client Deployment
*   **What:** Removed hardcoded URLs. Added required env vars: `MAKE_WEBHOOK_URL` (calendar integration), `CORE_API_URL` (API base URL). Updated `.env.example`, `docker-compose.yml`, and Python files to use these variables.
*   **Why:** Multi-client deployment. Each client needs unique Make.com webhook and potentially different API endpoints. Zero code changes per deployment now.

### [V2.4] - 2026-03-05 - Vapi Call Logging via Make.com
*   **What:** Created comprehensive implementation guide for logging Vapi voice calls to Sarah's database via Make.com webhooks (`voice-ai/VAPI_CALL_LOGGING.md`).
*   **Why:** Vapi voice calls need to be tracked in the CRM just like SMS conversations. 

### [V2.3] - 2026-03-04 - Function Calling (Tool Use) for Availability & Booking
*   **What:** Replaced the blind V2.2 webhook POST trigger with native OpenAI Function Calling (`manage_appointment`). 
*   **Why:** Make.com doesn't just receive leads; it checks calendar availability and returns it. 

### [V2.2] - 2026-03-04 - Make.com Booking Webhook Integration
*   **What:** Upgraded the LLM data extractor in `app.py` to identify if a lead explicitly requests an appointment, demo, or callback. If true, the system dynamically fires a POST request to the Make.com Webhook. 
*   **Why:** To transition leads instantly from "chatting via SMS" into the actual booking flow.

### [V2.1] - 2026-03-04 - API Endpoint Correction & Vapi Integration Documentation
*   **What:** Fixed API endpoint in `sarah_db_client.py` from `/context/{customer_id}/update` to `/conversation/{context_id}/update`. 
*   **Why:** Senior dev confirmed the correct endpoint is `/conversation/` not `/context/`.

### [V2.0] - 2026-03-04 - Dynamic LLM Follow-ups & CRM Extraction
*   **What:** Replaced hardcoded follow-up strings in `cron_worker.py` with LLM-generated texts via `generate_smart_followup()`. Created `followup_strategy.json`.
*   **Why:** To make follow-ups context-aware (V2 Architecture).

### [V1.1] - 2026-03-03 - API Routing Bugfix
*   **What:** Updated all Python files to pass `context_id` instead of `customer_id` into the `update_conversation` API call.
*   **Why:** The backend API strictly requires the UUID `context_id`.

### [V1.0] - 2026-02-26 - Initial State Machine Hack
*   **What:** Built the first iteration of the follow-up worker using the `intent` column as a state machine.
*   **Why:** The database lacked native automation-state fields.

---

## 🏗️ V2 Architecture (Current State)

We have moved from **Static Automation (V1)** to **Intelligent CRM Sync (V2)**.

1.  **Context-Aware Follow-ups:** `cron_worker.py` no longer sends dumb templates. It reads `followup_strategy.json` for *instructions* (e.g., "Send a casual bump"), reads the last 4 messages of the chat history, and asks OpenAI to draft a personalized SMS that perfectly matches the context.
2.  **Dynamic Strategy:** Timing and AI instructions are fully decoupled from Python. They live in `followup_strategy.json` for easy editing.
3.  **Auto-Enrichment & Scoring:** When the Twilio webhook (`app.py`) receives a message, the LLM prompt not only generates a reply and summary, but explicitly extracts `extracted_name`, `extracted_email`, `interest_level` (hot/warm/cold), `product_interest`, and `call_recommended` flags to update the core database.

---

## 🚀 OPS DEPLOYMENT NOTES (V2.5/2.6 Changes)

### **New Environment Variables Required:**

```bash
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod  # Optional (has default)
MAKE_WEBHOOK_URL=https://hook.us2.make.com/client_webhook_id                  # REQUIRED per client
OPENAI_MODEL=gpt-5.2                                                          # REQUIRED (Tool calling depends on this format)
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
Handles incoming SMS, generates AI responses, extracts CRM data. Deploy via SOP script: `./deploy.sh`

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
