# Sarah AI - Technical Specification for Developer Handoff

**Created:** 2026-03-15  
**Author:** Bo (Architect) + Shiva (Product Owner)  
**Target Launch:** March 19, 2026  
**Current Status:** 85% Complete

---

## 📋 Executive Summary

Sarah is an AI-powered SMS + Voice follow-up agent for real estate lead nurturing. The system receives inbound SMS/voice, generates AI responses, logs to a CRM backend (Sarah DB), and autonomously sends follow-ups to unresponsive leads.

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                         INBOUND CHANNELS                             │
├──────────────────┬──────────────────────────────────────────────────┤
│   Twilio SMS     │              Vapi Voice                          │
│   (/sms/inbound) │         (via Make.com webhook)                   │
└────────┬─────────┴───────────────────┬──────────────────────────────┘
         │                             │
         ▼                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FLASK APP (app.py)                           │
│  - Receives webhook                                                 │
│  - Calls Sarah DB API for context                                  │
│  - Generates AI reply (OpenAI + Function Calling)                  │
│  - Logs messages + updates conversation state                       │
│  - Sends reply via Twilio                                          │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SARAH DB (AWS API Gateway + Lambda)            │
│  Base: https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod │
│                                                                     │
│  Endpoints:                                                        │
│  - GET  /context/{id}?by=phone_normalized  → Customer context      │
│  - POST /log                               → Log messages          │
│  - POST /conversation/{context_id}/update  → Update state          │
│  - POST /customers                         → Create customer       │
│  - PUT  /customers/{id}                    → Update customer       │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CRON WORKER (cron_worker.py)                    │
│  - Runs every 5 minutes                                            │
│  - Checks for unresponsive leads (based on followup_strategy.json) │
│  - Generates AI follow-ups                                         │
│  - Sends SMS via Twilio                                            │
│  - Transitions conversation intent state                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔴 CRITICAL BUGS TO FIX

### Bug #1: Voice → SMS Flow Broken

**Symptom:** Voice calls via Vapi are NOT triggering SMS follow-ups.

**Root Cause (Suspected):**
1. Make.com scenario calls WRONG endpoint for context update
2. The voice-ai README shows: `POST /context/{customer_id}/update` ❌
3. Correct endpoint is: `POST /conversation/{context_id}/update` ✅

**Location:** `voice-ai/README.md` line showing architecture
```
# WRONG (in README)
3. Update Context → POST /context/{customer_id}/update

# CORRECT
3. Update Context → POST /conversation/{context_id}/update
```

**Fix Required:**
1. Update Make.com scenario (call-ended.json) to use `/conversation/{context_id}/update`
2. Ensure Make.com extracts `context_id` (UUID) not `customer_id` (int) from the `/context/{phone}` response
3. Update `voice-ai/README.md` to document correct endpoint

**Files to Modify:**
- `voice-ai/make-scenario/call-ended.json`
- `voice-ai/README.md`
- Make.com dashboard scenario

---

### Bug #2: Name and Email Update Not Working Reliably

**Symptom:** When user provides name/email in SMS, it doesn't always update the customer record.

**Root Cause (Suspected):**
The `update_customer()` call in `app.py` may be failing silently. The PUT endpoint may not exist or return 405.

**Location:** `app.py` lines ~280-286
```python
if ext_name or ext_email:
    print(f"DEBUG: Found new customer info - Name: {ext_name}, Email: {ext_email}")
    try:
        db_client.update_customer(customer_id=customer_id, name=ext_name, email=ext_email)
    except Exception as ce:
        print(f"DEBUG: Failed to update customer profile: {ce}")
```

**Fix Required:**
1. Verify `PUT /customers/{id}` endpoint exists in backend
2. If not, create it OR use alternate approach (PATCH or re-POST)
3. Add better error logging to identify the actual failure

**Files to Modify:**
- `sarah_db_client.py` - Verify endpoint behavior
- Backend API (if endpoint missing)

---

### Bug #3: Warm Transfer Not Implemented

**Symptom:** User says "talk to human" or "call me" but handoff doesn't actually happen.

**Current State:** `app.py` sends a message saying "A member of our team will call you shortly" but doesn't actually notify anyone.

**Location:** `app.py` lines ~227-236
```python
if any(k in normalized_body for k in ["HUMAN", "CALL ME"]):
    reply_text = "I've noted your request. A member of our team will call you shortly."
    # ... logs it but does NOT notify a human
```

**Fix Required:**
1. Send notification to Telegram/Slack/Email when handoff requested
2. OR trigger a webhook to alert CRM/sales team
3. Set intent to `HANDOFF_REQUESTED` to stop automation

**Proposed Solution:**
```python
# Add after logging handoff
webhook_url = os.getenv("HANDOFF_WEBHOOK_URL")
if webhook_url:
    requests.post(webhook_url, json={
        "type": "handoff_requested",
        "phone": sender,
        "customer_id": customer_id,
        "timestamp": datetime.now().isoformat()
    })
```

**Files to Modify:**
- `app.py` - Add notification logic
- `.env` - Add HANDOFF_WEBHOOK_URL

---

## 🟡 IMPROVEMENTS NEEDED

### Improvement #1: GET /conversations Endpoint Returns 403

**Current Workaround:** `cron_worker.py` fetches ALL customers, then loops through each to get context. This is O(N) API calls instead of O(1).

**Impact:** Slow, wasteful, will break at scale.

**Fix Required (Backend):**
- Grant API key permissions for `GET /conversations?status=active`
- OR create a new endpoint that returns all active conversations

**Workaround File:** `cron_worker.py` lines ~52-70

---

### Improvement #2: State Machine via Intent Field (Hack)

**Current State:** The database lacks `automation_status` or `followup_count` fields. We use the `intent` field as a state machine:

```
WAITING_FOR_ANSWER → FOLLOWUP_1 → FOLLOWUP_2 → NURTURE
       ↑                                          
       └── ENGAGED (user replied, stops automation)
       └── HOT_LEAD (booking requested, stops automation)
```

**Problem:** Mixing business intent with automation state is fragile.

**Recommended Backend Fix:**
Add columns to Conversations table:
- `automation_status` (enum: active, paused, stopped)
- `followup_count` (int)
- `next_followup_at` (timestamp)

---

### Improvement #3: Booking Flow Hardcoded to Make.com

**Location:** `app.py` line ~150
```python
webhook_url = "https://hook.us2.make.com/upoequuxi2bbqc68j07o9b6i552dr951"
```

**Fix:** Move to environment variable
```python
webhook_url = os.getenv("BOOKING_WEBHOOK_URL")
```

---

## 🟢 CODE QUALITY ISSUES

### Issue #1: Duplicate Entry Points

Both `app.py` and `main.py` handle SMS inbound. This is confusing.

**Recommendation:** 
- Keep `app.py` (full featured)
- Remove or deprecate `main.py` (simplified)
- OR clearly document when to use which

### Issue #2: config.py is Empty

File exists but contains nothing. Either use it or delete it.

### Issue #3: Error Handling Swallows Exceptions

Multiple places have:
```python
except Exception as e:
    print(f"DEBUG: Error: {e}")
    pass  # silently continues
```

**Recommendation:** Add proper logging with severity levels, consider alerting on critical failures.

---

## 📁 FILE STRUCTURE REFERENCE

```
Follow-up_agent/
├── app.py                 # Main Flask app (SMS inbound webhook)
├── main.py                # Simplified inbound handler (deprecated?)
├── cron_worker.py         # Scheduled follow-up sender
├── sarah_db_client.py     # API client for Sarah DB
├── tasks.py               # RQ task definitions (scheduled jobs)
├── utils.py               # Logging helpers
├── config.py              # Empty - delete or populate
├── followup_strategy.json # Timing rules for follow-ups
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Multi-container setup
├── .env                   # Environment variables (not in git)
│
├── docs/
│   ├── README_DEVELOPER.md     # Dev handoff guide
│   ├── AGENTS.md               # Agent architecture
│   ├── API_REFERENCE.md        # Quick API reference
│   ├── ENDPOINT_REFERENCE.md   # Detailed endpoint docs
│   ├── API Usage Guide_v2.md   # Full API documentation
│   ├── DEPLOYMENT_SOP.md       # Deployment procedures
│   └── DASHBOARD_PLAN.md       # Future dashboard specs
│
└── voice-ai/
    ├── README.md               # Voice integration overview
    ├── make-scenario/
    │   ├── incoming-call.json  # Make.com scenario (import)
    │   ├── call-ended.json     # Make.com scenario (import)
    │   └── setup.md            # Setup instructions
    ├── vapi-setup/
    │   └── configuration.md    # Vapi webhook config
    └── api/
        └── *.json              # API call templates
```

---

## 🔧 ENVIRONMENT VARIABLES REQUIRED

```bash
# Core API
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
CORE_API_KEY=your_api_key

# Twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# OpenAI
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini

# Redis (for RQ worker)
REDIS_URL=redis://localhost:6379/0

# Agent Config
AGENT_NAME=Sarah

# Webhooks (NEW - need to add)
BOOKING_WEBHOOK_URL=https://hook.us2.make.com/xxxxx
HANDOFF_WEBHOOK_URL=https://hook.us2.make.com/xxxxx  # For human handoff alerts
```

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Launch (by Mar 18)
- [ ] Fix Voice → SMS endpoint in Make.com
- [ ] Fix name/email update (verify PUT endpoint)
- [ ] Add handoff notification webhook
- [ ] Move hardcoded webhook URL to .env
- [ ] Test full flow: Voice call → Context lookup → Log → SMS follow-up

### Launch Day (Mar 19)
- [ ] Run `docker-compose up -d --build`
- [ ] Verify cron job running: `*/5 * * * * python3 cron_worker.py`
- [ ] Test with live phone call
- [ ] Monitor logs for errors

### Post-Launch
- [ ] Set up log aggregation (CloudWatch/Datadog)
- [ ] Add alerting for failures
- [ ] Document runbook for on-call

---

## 📞 CONTACT

- **Product Owner:** Shiva (sivakumar@kalkiaevolutionia.com)
- **Architect:** Bo (OpenClaw)
- **Code Repository:** `~/.openclaw/workspace/Follow-up_agent/`

---

*This document is the single source of truth for the Sarah AI technical spec. Update it as changes are made.*
