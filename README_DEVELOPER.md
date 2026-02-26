# Sarah Follow-Up Agent - Developer Handoff 🤖

## 📋 Overview
This is a lightweight automation agent designed to send SMS follow-ups to leads based on their responsiveness. It interacts with the Core API (Sarah DB) and Twilio.

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- `pip`
- Valid Core API Key (`x-api-key`)
- Twilio Account SID/Auth Token

### 2. Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install requests python-dotenv twilio
```

### 3. Configuration (.env)
Create a `.env` file in this directory:
```ini
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
CORE_API_KEY=your_actual_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
AGENT_NAME=Sarah
```

### 4. Running the Automation
The system has two parts:

**A. Inbound Webhook (`main.py`)**
Handles incoming SMS replies to stop automation.
```bash
# Run with Flask/Gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 main:app
```

**B. Outbound Worker (`cron_worker.py`)**
Checks for unresponsive leads and sends follow-ups. Designed to run via Cron.
```bash
# Manual run
python3 cron_worker.py

# Cron setup (Every 5 mins)
*/5 * * * * /path/to/venv/bin/python /path/to/cron_worker.py >> /var/log/sarah.log 2>&1
```

---

## 🏗️ Architecture & "Hacks" (Important!)

### 1. State Machine via `intent` Field
**Context:** The Core DB schema does NOT have native fields for `automation_status` or `followup_count`.
**The Hack:** We utilize the **`intent`** field in the conversation context to track the automation state.

| State / Intent | Meaning | Action |
| :--- | :--- | :--- |
| `WAITING_FOR_ANSWER` | AI asked a question, waiting for user. | If >30m, send Follow-up 1. |
| `FOLLOWUP_1` | First nudge sent. | If >24h, send Follow-up 2. |
| `FOLLOWUP_2` | Second nudge sent. | If >24h, move to NURTURE. |
| `NURTURE` | Lead unresponsive (Soft Close). | No action. |
| `ENGAGED` | User replied. | **Stop Automation.** |

**Logic Location:** `cron_worker.py` handles the state transitions. `main.py` resets state to `ENGAGED` on reply.

### 2. API Endpoint Workaround
**Issue:** The endpoint `GET /conversations?status=active` currently returns **403 Forbidden** with the provided API key.
**Workaround:** The worker (`cron_worker.py`) instead calls **`GET /customers`** (iterates all customers) and then fetches `GET /context/{id}` for each one individually.
**Impact:** This is inefficient (O(N) API calls).
**Fix Needed:** Grant correct permissions for `GET /conversations` to the API Key, then revert `cron_worker.py` to use the batch endpoint.

### 3. Dependencies
The original `requirements.txt` might be outdated. Ensure `twilio`, `requests`, and `python-dotenv` are installed.

---

## 📂 Key Files
*   `cron_worker.py`: The brain. Checks timestamps vs state and sends SMS.
*   `sarah_db_client.py`: Wrapper for Core API.
*   `main.py`: Flask webhook for inbound Twilio messages.
