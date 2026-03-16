# Sarah AI - System Architecture v2.0
## OpenClaw Brain Integration

**Version:** 2.0  
**Created:** 2026-03-15  
**Updated:** 2026-03-16 (OpenClaw Brain Integration)  
**Authors:** Shiva (Product), Bo (Architecture)  
**Status:** 🔴 Architecture Review - Pending Approval

---

## Executive Summary

Sarah v2.0 adopts a **hybrid architecture** that combines:
- **Python Shell** (outer layer): Proven channel handlers, scheduling, CRM integration  
- **TypeScript Brain** (core): Extracted OpenClaw components for AI decision-making

This design leverages OpenClaw's production-tested agent runtime (~8,000 lines of battle-tested code) while keeping Sarah's specialized sales logic and multi-lead parallel processing intact.

**Key Decision:** Extract only OpenClaw's "brain" (agent runtime, memory system, session management) instead of adopting its full channel infrastructure, which is designed for single-user personal assistant use cases.

---

## 1. Vision

Sarah is an **autonomous AI Sales Agent** that lives inside a business. She handles inbound/outbound communication across SMS, Voice, and Email — making intelligent decisions about when, how, and what to say to each lead.

Unlike a chatbot that just responds, Sarah:
- **Orchestrates** across channels (decides SMS vs call vs email)
- **Learns** from each business over 1-2 months
- **Adapts** her communication style per lead
- **Reports** to the business owner through familiar channels

**Architecture Philosophy:**
- **Python handles I/O** (webhooks, API calls, scheduling) — what Sarah does best today
- **TypeScript handles intelligence** (AI decisions, memory, learning) — what OpenClaw does best
- **Simple HTTP API** connects the two layers — clean separation of concerns
- **Hybrid storage** — brain.db for speed, Sarah DB for persistence

---

## 2. Design Principles

| Principle | Implementation |
|-----------|----------------|
| **CRM-Agnostic** | Python adapters for Zoho, Salesforce, HubSpot (Sarah DB abstraction) |
| **Channel-Agnostic** | Python handlers for SMS, Voice, Email — Brain decides, Python executes |
| **Living Memory** | OpenClaw memory system (vector embeddings, hybrid search, pattern matching) |
| **Owner-Accessible** | Telegram bot for owner commands, alerts, pipeline queries |
| **Auditable** | All decisions logged to Sarah DB with reasoning traces |
| **Production-Tested** | OpenClaw runtime = 3k+ GitHub stars, active development, proven at scale |

---

## 3. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           BUSINESS OWNER                                 │
│                    (Telegram / iMessage / Email)                         │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    PYTHON LAYER (Sarah Shell)                            │
│                         Port 5000/5001                                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Channel Handlers (Proven, Working Code)                        │    │
│  │  • app.py - SMS webhooks (Twilio)                              │    │
│  │  • vapi_handler.py - Voice webhooks (Vapi) [NEW]               │    │
│  │  • cron_worker.py - Scheduled follow-up checks                  │    │
│  │  • nightly_learning.py - Batch learning indexer [NEW]           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Sarah Orchestrator (Coordinator) [NEW]                         │    │
│  │  • Fetches context from Sarah DB                                │    │
│  │  • Calls OpenClaw Brain for decisions                           │    │
│  │  • Executes actions (SMS, Call, Escalate)                       │    │
│  │  • Logs to Sarah DB                                             │    │
│  │  • Handles Brain API failures with fallback                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ HTTP localhost:3000
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   TYPESCRIPT LAYER (OpenClaw Brain)                      │
│                           Port 3000                                      │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │  Decision      │  │  Memory &      │  │  Learning      │             │
│  │  Engine        │  │  Context       │  │  Module        │             │
│  │                │  │                │  │                │             │
│  │ • Agent Runtime│  │ • Session Mgmt │  │ • Vector Search│             │
│  │ • Multi-model  │  │ • Transcripts  │  │ • Embeddings   │             │
│  │ • Tool Calling │  │ • Compaction   │  │ • Pattern Match│             │
│  │ • Failover     │  │ • Token Budget │  │ • Hybrid Search│             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
│  🧠 Extracted from OpenClaw (github.com/openclaw/openclaw):            │
│     • pi-embedded-runner.ts - Agent execution engine                    │
│     • memory/ - Vector embeddings, SQLite-vec, hybrid search            │
│     • sessions/ - Conversation management, context windows              │
│     • model-fallback.ts - Multi-provider failover                       │
│                                                                          │
│  💾 Local Storage: brain.db (SQLite + sqlite-vec)                      │
│     • Active sessions (last 50 messages per lead)                       │
│     • Vector embeddings (learning patterns from closed conversations)   │
│     • 7-day message retention, nightly pruning                          │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  SMS Channel  │          │ Voice Channel │          │ Email Channel │
│   (Twilio)    │          │    (Vapi)     │          │  (SendGrid)   │
│   Python      │          │   Python      │          │   Planned     │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER (Hybrid)                              │
│                                                                          │
│  ┌─────────────────────────┐       ┌─────────────────────────┐          │
│  │    SARAH DB (API)       │       │  brain.db (SQLite)      │          │
│  │  (Long-term Storage)    │       │  (Short-term Cache)     │          │
│  │   AWS Lambda Gateway    │       │   Local to Brain        │          │
│  │                         │       │                         │          │
│  │ • Full conversation     │       │ • Active sessions       │          │
│  │   history (forever)     │       │ • Recent messages (7d)  │          │
│  │ • Customer/Lead records │       │ • Vector embeddings     │          │
│  │ • Decision logs         │       │ • Learning patterns     │          │
│  │ • CRM sync data         │       │                         │          │
│  │                         │  ◄──  │ Nightly sync:          │          │
│  │ ✅ Source of Truth      │       │ - Index closed convos   │          │
│  │                         │       │ - Prune old sessions    │          │
│  └─────────────────────────┘       └─────────────────────────┘          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Key Changes from v1.0:**
1. ✅ **Split Architecture** - Python shell + TypeScript brain (HTTP API boundary)
2. ✅ **Proven Channels Stay** - SMS/Voice handlers remain in Python (working code)
3. ✅ **OpenClaw Brain** - Extracted agent runtime, memory, sessions (production-tested)
4. ✅ **Hybrid Storage** - brain.db for speed/intelligence, Sarah DB for persistence/audit
5. ✅ **No Gateway Bloat** - Only brain components extracted, not full OpenClaw platform

---

## 4. Component Details

### 4.1 Python Layer - Sarah Orchestrator

**Purpose:** Coordinate between channel handlers and OpenClaw Brain

**Location:** `sarah_orchestrator.py` (NEW file)

**Responsibilities:**
1. Receive events from channel handlers (SMS, Voice, Cron)
2. Fetch lead context from Sarah DB
3. Call OpenClaw Brain API for decision
4. Execute decision (send SMS, trigger call, notify owner)
5. Log all interactions to Sarah DB
6. Handle Brain API failures with fallback logic

**API Interface to Brain:**
```python
class OpenClawBrainClient:
    def decide(self, lead_context: dict, user_message: str, channel: str) -> dict:
        """
        POST http://localhost:3000/decide
        
        Request:
        {
            "lead_context": {
                "customer_id": 123,
                "phone": "+15551234567",
                "name": "John Doe",
                "intent": "WAITING_FOR_ANSWER",
                "sentiment": "neutral",
                "last_interaction_at": "2026-03-16T10:30:00Z",
                "conversation_history": [...]
            },
            "user_message": "Hi, I'm interested in...",
            "channel": "sms"
        }
        
        Response:
        {
            "action": "SMS" | "CALL" | "WAIT" | "ESCALATE" | "STOP",
            "message": "Generated reply text",
            "reasoning": "Lead asked about pricing, showing intent...",
            "new_intent": "HOT_LEAD",
            "sentiment": "positive",
            "schedule_delay": null
        }
        """
```

**Fallback Logic (if Brain API fails):**
```python
def _fallback_reply(self, phone, body):
    """Simple rule-based fallback if Brain is down"""
    if any(word in body.lower() for word in ["pricing", "price", "cost"]):
        return "Thanks for your interest! A team member will reach out shortly."
    elif any(word in body.lower() for word in ["not interested", "stop"]):
        self.db.update_conversation(intent="CLOSED_LOST")
        return "Understood. We've noted your preference."
    else:
        return "Thanks for your message. We'll get back to you soon."
```

---

### 4.2 TypeScript Layer - OpenClaw Brain

**Purpose:** Intelligent decision-making engine powered by OpenClaw's agent runtime

**Location:** `openclaw-brain/` (NEW directory)

**Core Components (Extracted from OpenClaw):**

#### **A. Agent Runtime** (`src/agents/pi-embedded-runner.ts`)
- Executes AI models (Claude, GPT, Gemini, etc.)
- Manages conversation context windows
- Handles tool calling (OpenAI function calling pattern)
- Implements retry logic and model failover
- Tracks token usage and costs

#### **B. Memory System** (`src/memory/`)
- Vector embeddings (OpenAI, Voyage, Gemini, Ollama providers)
- SQLite-vec for fast similarity search
- Hybrid search (vector + keyword)
- Indexes successful conversation patterns
- Searches for similar past interactions

#### **C. Session Management** (`src/sessions/`)
- Tracks active conversations per lead
- Manages message history
- Handles context window compaction (summarize old messages)
- Session isolation (one session per phone number)

#### **D. Sarah-Specific Tools** (`tools/`)

**Tool 1: decide_next_action.ts**
```typescript
// Core decision logic (maps to Section 4.1 Decision Rules)
export const decideNextActionTool = {
  name: "decide_next_action",
  description: `Analyze lead state and decide next action based on Sarah's rules.
  
  Decision Matrix:
  - Lead replied positively → ESCALATE to owner
  - No response < 30min → WAIT
  - No response 30min-24hr → SMS follow-up #1
  - No response 24hr-72hr → SMS follow-up #2  
  - No response > 72hr → CALL via Vapi
  - Lead said "not interested" → STOP
  - Lead booked appointment → ESCALATE
  - High intent keywords detected → ESCALATE
  `,
  parameters: {
    type: "object",
    properties: {
      lead_state: { /* customer_id, intent, sentiment, etc. */ },
      time_since_last_interaction: { type: "number" }, // seconds
      conversation_summary: { type: "string" },
      channel_history: { /* response rates per channel */ }
    }
  },
  handler: async (params) => {
    // Decision logic implementation
    const { lead_state, time_since_last_interaction } = params;
    
    // Check for hot lead signals
    if (lead_state.intent === "HOT_LEAD" || detectBookingIntent(params.conversation_summary)) {
      return { action: "ESCALATE", reason: "Booking requested" };
    }
    
    // Check for negative signals
    if (lead_state.sentiment === "negative" || detectUninterested(params.conversation_summary)) {
      return { action: "STOP", reason: "Lead not interested" };
    }
    
    // Time-based follow-up logic
    const minutes = time_since_last_interaction / 60;
    if (minutes < 30) return { action: "WAIT", schedule_delay: 30 - minutes };
    if (minutes < 1440) return { action: "SMS", message: generateFollowup1(lead_state) };
    if (minutes < 4320) return { action: "SMS", message: generateFollowup2(lead_state) };
    
    return { action: "CALL", reason: "No response after 72 hours" };
  }
};
```

**Tool 2: search_similar_conversations.ts**
```typescript
// Leverage memory system for pattern matching
export const searchSimilarConversationsTool = {
  name: "search_similar_conversations",
  description: "Find similar past conversations to learn from successful patterns",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string" },
      lead_type: { type: "string" },
      outcome_filter: { type: "string", enum: ["won", "lost", "any"] }
    }
  },
  handler: async (params) => {
    const memory = await getMemorySearchManager();
    const results = await memory.search(params.query, { limit: 5 });
    
    return {
      similar_conversations: results
        .filter(r => params.outcome_filter === "any" || r.metadata.outcome === params.outcome_filter)
        .map(r => ({
          message: r.text,
          outcome: r.metadata.outcome,
          similarity: r.score,
          lead_type: r.metadata.lead_type,
          what_worked: r.metadata.what_worked
        }))
    };
  }
};
```

**HTTP API Wrapper** (`src/sarah-brain-api.ts`)
```typescript
import express from 'express';
import { runEmbeddedPiAgent } from './agents/pi-embedded.js';
import { sarahTools } from '../tools/index.js';

const app = express();
app.use(express.json());

app.post('/decide', async (req, res) => {
  const { lead_context, user_message, channel } = req.body;
  
  const systemPrompt = buildSarahPrompt(lead_context);
  
  const response = await runEmbeddedPiAgent({
    sessionKey: lead_context.phone,
    userMessage: user_message,
    systemPrompt,
    tools: sarahTools,
    model: 'anthropic/claude-sonnet-4',
    context: lead_context.conversation_history
  });
  
  res.json(response);
});

app.post('/learn', async (req, res) => {
  const { conversation_id, outcome, messages } = req.body;
  
  const memory = await getMemorySearchManager();
  for (const msg of messages) {
    await memory.index(msg.body, {
      conversation_id,
      outcome,
      lead_type: msg.lead_type,
      sentiment: msg.sentiment
    });
  }
  
  res.json({ indexed: messages.length });
});

app.listen(3000);
```

---

### 4.3 Channel Handlers (Python)

#### **SMS Handler** (`app.py` - MODIFIED)

```python
from sarah_orchestrator import SarahOrchestrator

orchestrator = SarahOrchestrator()

@app.route('/sms/inbound', methods=['POST'])
def handle_inbound_sms():
    from_phone = request.form.get('From')
    body = request.form.get('Body')
    
    # Delegate to orchestrator
    orchestrator.handle_inbound_sms(from_phone, body)
    
    return str(MessagingResponse())
```

#### **Voice Handler** (`vapi_handler.py` - NEW)

```python
from flask import Flask, request, jsonify
from sarah_orchestrator import SarahOrchestrator

vapi_app = Flask(__name__)
orchestrator = SarahOrchestrator()

@vapi_app.route('/vapi/call-started', methods=['POST'])
def handle_call_started():
    """Vapi calls this when call starts - return lead context"""
    phone = request.json.get('phone')
    context = orchestrator.db.get_context(phone)
    return jsonify(context)

@vapi_app.route('/vapi/call-ended', methods=['POST'])
def handle_call_ended():
    """Vapi calls this when call ends - process transcript"""
    call_data = request.json
    orchestrator.handle_inbound_voice(call_data)
    return jsonify({"status": "ok"})
```

#### **Cron Worker** (`cron_worker.py` - SIMPLIFIED)

```python
from sarah_orchestrator import SarahOrchestrator

def check_unresponsive_leads():
    orchestrator = SarahOrchestrator()
    orchestrator.check_followups_due()

if __name__ == "__main__":
    check_unresponsive_leads()
```

#### **Nightly Learning** (`nightly_learning.py` - NEW)

```python
"""
Nightly job: Index closed conversations into Brain memory
Schedule: 0 2 * * * (2 AM daily)
"""
import requests
from sarah_db_client import SarahDBClient

def index_closed_conversations():
    db = SarahDBClient()
    brain_url = "http://localhost:3000"
    
    # Get conversations closed in last 24 hours with positive outcomes
    closed_convos = db.get_closed_conversations(
        since_hours=24,
        outcomes=["CLOSED_WON", "HOT_LEAD"]
    )
    
    for convo in closed_convos:
        # Index successful patterns
        requests.post(f"{brain_url}/learn", json={
            "conversation_id": convo["conversation_id"],
            "outcome": convo["outcome"],
            "messages": convo["messages"]
        })
    
    print(f"Indexed {len(closed_convos)} successful conversations")
```

---

### 4.4 Data Layer (Hybrid Storage)

#### **Short-term Storage: brain.db (SQLite + sqlite-vec)**

**Location:** `openclaw-brain/data/brain.db`

**Purpose:** Fast access for active conversations and pattern matching

**Schema:**
```sql
-- Active conversation sessions
CREATE TABLE sessions (
    session_key TEXT PRIMARY KEY,      -- phone number
    customer_id INTEGER,
    last_interaction TIMESTAMP,
    message_count INTEGER,
    created_at TIMESTAMP
);

-- Recent messages (7-day retention)
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    session_key TEXT,
    role TEXT,                         -- 'user' | 'assistant'
    content TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (session_key) REFERENCES sessions(session_key)
);

-- Vector embeddings for similarity search
CREATE VIRTUAL TABLE embeddings USING vec0(
    embedding_id TEXT PRIMARY KEY,
    vector FLOAT[1536],                -- OpenAI ada-002 dimensions
    text TEXT,
    metadata JSON                      -- { outcome, lead_type, sentiment }
);
```

**Retention Policy:**
- **Sessions:** Active + 7 days after last interaction
- **Messages:** 7 days rolling window
- **Embeddings:** Indefinite (learning data)
- **Pruning:** Nightly via `nightly_learning.py`

#### **Long-term Storage: Sarah DB (AWS API Gateway + Lambda)**

**Access:** Via `sarah_db_client.py` → `https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod`

**Purpose:** Persistent storage, audit trail, CRM sync

**Responsibilities:**
- Full conversation history (all messages, forever)
- Customer/Lead records
- Decision logs (action + reasoning)
- CRM integration data
- Closed conversation outcomes

**Sync Strategy:**
```
Python Layer       →  Sarah DB  (immediate - every interaction)
Sarah DB          →  brain.db  (nightly - closed conversations only)
brain.db          ↔  Memory    (real-time - active sessions)
```

---

## 5. Data Flow Examples

### 5.1 Inbound SMS (New Flow with Brain)

```
1. Lead sends SMS to Twilio number
2. Twilio webhook → app.py (/sms/inbound)
3. app.py → sarah_orchestrator.handle_inbound_sms(phone, body)
4. Orchestrator:
   a. Fetch context: sarah_db.get_context(phone)
   b. Call Brain: brain_api.decide(context, body, "sms")
5. Brain (OpenClaw):
   a. Load session from brain.db
   b. Run agent with Sarah tools (decide_next_action, search_similar, etc.)
   c. Agent returns: { action: "SMS", message: "...", reasoning: "..." }
6. Orchestrator:
   a. Execute: twilio.send_sms(phone, message)
   b. Log: sarah_db.log_message(customer_id, "in", body)
   c. Log: sarah_db.log_message(customer_id, "out", message)
   d. Update: sarah_db.update_conversation(context_id, intent, sentiment)
7. Return 200 OK to Twilio
```

**Performance:** < 5 seconds end-to-end (webhook → reply sent)

---

### 5.2 Inbound Voice Call (Replaces Make.com)

```
1. Lead calls Vapi number
2. Vapi webhook → vapi_handler.py (/vapi/call-started)
3. vapi_handler:
   a. Fetch context: sarah_db.get_context(phone)
   b. Return context to Vapi (name, company, last interaction, sentiment)
4. Vapi conducts conversation using context
5. Call ends → Vapi webhook → vapi_handler.py (/vapi/call-ended)
6. vapi_handler → sarah_orchestrator.handle_inbound_voice(call_data)
7. Orchestrator:
   a. Call Brain: brain_api.decide(context, transcript, "voice")
   b. Brain analyzes: sentiment, intent, next action
   c. Log: sarah_db.log_message(customer_id, "voice", transcript)
8. If action = "SMS":
   a. Schedule follow-up (30 min delay to avoid immediate SMS after call)
   b. cron_worker will send at scheduled time
```

---

### 5.3 Scheduled Follow-up (Cron)

```
1. Cron triggers: */5 * * * * (every 5 minutes)
2. cron_worker.py → orchestrator.check_followups_due()
3. Orchestrator:
   a. Fetch all active leads: sarah_db.list_customers()
   b. For each lead:
      - Fetch context: sarah_db.get_context(customer_id)
      - Ask Brain: "Should I follow up with this lead now?"
      - Brain uses decide_next_action tool with time_since_last_interaction
4. Brain returns: { action: "SMS" | "CALL" | "WAIT" | "STOP" }
5. Orchestrator executes:
   - If SMS: send message, log, update intent to "FOLLOWUP_1"
   - If CALL: trigger Vapi outbound call
   - If WAIT: skip, check again in 5 min
   - If STOP: mark CLOSED_LOST
```

---

### 5.4 Nightly Learning (Batch Job)

```
1. Cron triggers: 0 2 * * * (2 AM daily)
2. nightly_learning.py runs
3. Fetch closed conversations:
   - sarah_db.get_closed_conversations(since_hours=24, outcomes=["CLOSED_WON"])
4. For each successful conversation:
   a. POST brain_api/learn with messages
   b. Brain indexes into embeddings table (vector search)
5. Prune old sessions:
   - DELETE FROM brain.sessions WHERE last_interaction < NOW() - 7 days
6. Generate learning report:
   - Patterns discovered
   - Conversion improvements
   - Message effectiveness
```

---

## 6. Configuration

### 6.1 Python Layer (.env)

```bash
# Existing
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
CORE_API_KEY=your_api_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# New
OPENCLAW_BRAIN_URL=http://localhost:3000
VAPI_API_KEY=your_vapi_key
VAPI_PHONE_NUMBER=your_vapi_number
TELEGRAM_BOT_TOKEN=your_bot_token
OWNER_TELEGRAM_ID=8290509439
```

### 6.2 TypeScript Brain (openclaw-brain/.env)

```bash
# Model providers
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key  # For Gemini

# Default model
DEFAULT_MODEL=anthropic/claude-sonnet-4

# Database
DATABASE_PATH=./data/brain.db

# API
PORT=3000
LOG_LEVEL=info
```

### 6.3 Sarah Agent Configuration (openclaw-brain/config/sarah-agent-config.json)

```json
{
  "agent": {
    "name": "Sarah",
    "model": "anthropic/claude-sonnet-4",
    "systemPromptTemplate": "You are Sarah, an AI Sales Agent for {{business_name}}...",
    "maxTokens": 2000,
    "temperature": 0.7
  },
  "tools": [
    "decide_next_action",
    "search_similar_conversations",
    "detect_intent",
    "extract_contact_info",
    "analyze_sentiment"
  ],
  "memory": {
    "enabled": true,
    "embeddingModel": "openai/text-embedding-3-small",
    "hybridSearchWeight": 0.7,  // 70% vector, 30% keyword
    "topK": 5
  },
  "session": {
    "maxMessages": 50,
    "compactionThreshold": 40,  // Summarize when > 40 messages
    "retentionDays": 7
  },
  "fallback": {
    "model": "openai/gpt-4o-mini",
    "retryAttempts": 3,
    "retryDelayMs": 1000
  }
}
```

---

## 7. Deployment Architecture

### 7.1 Single VPS Deployment (Recommended for MVP)

```
┌─────────────────────────────────────────────────────────────┐
│                     VPS (Ubuntu 22.04)                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Python Services                                     │   │
│  │  • Flask (app.py) - Port 5000                       │   │
│  │  • Vapi Handler - Port 5001                         │   │
│  │  • Gunicorn (4 workers)                             │   │
│  │  • Systemd service: sarah-python.service            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Node.js Service                                     │   │
│  │  • OpenClaw Brain API - Port 3000                   │   │
│  │  • PM2 / Systemd service: openclaw-brain.service    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Redis                                               │   │
│  │  • Port 6379 (job queue for RQ)                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cron Jobs                                           │   │
│  │  • */5 * * * * python3 cron_worker.py               │   │
│  │  • 0 2 * * * python3 nightly_learning.py            │   │
│  │  • 0 3 * * * backup brain.db                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  📁 Data: /home/ubuntu/Follow-up_agent/openclaw-brain/data │
│  📁 Logs: /var/log/sarah/                                  │
│  📁 Backups: /home/ubuntu/backups/                         │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Docker Compose Deployment (Alternative)

```yaml
version: '3.8'

services:
  sarah-python:
    build: .
    ports:
      - "5000:5000"
      - "5001:5001"
    environment:
      - OPENCLAW_BRAIN_URL=http://openclaw-brain:3000
    volumes:
      - .:/app
    depends_on:
      - openclaw-brain
      - redis

  openclaw-brain:
    build: ./openclaw-brain
    ports:
      - "3000:3000"
    volumes:
      - ./openclaw-brain/data:/app/data
    environment:
      - DATABASE_PATH=/app/data/brain.db

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  cron-worker:
    build: .
    volumes:
      - .:/app
    depends_on:
      - sarah-python
      - openclaw-brain
    command: python3 cron_worker.py
```

---

## 8. Migration Path (v1 → v2)

### Phase 1: Extract OpenClaw Brain (Week 1)
- [x] Clone OpenClaw repo
- [ ] Create `openclaw-brain/` directory structure
- [ ] Copy extracted files (agent, memory, sessions)
- [ ] Build sarah-brain-api.ts HTTP wrapper
- [ ] Create Sarah-specific tools
- [ ] Test Brain API standalone

### Phase 2: Python Integration (Week 2)
- [ ] Create sarah_orchestrator.py
- [ ] Create vapi_handler.py (replace Make.com)
- [ ] Create nightly_learning.py
- [ ] Update app.py to use orchestrator
- [ ] Update cron_worker.py
- [ ] Test locally (both services)

### Phase 3: Deploy & Test (Week 3)
- [ ] Deploy to VPS
- [ ] Configure systemd services
- [ ] Setup cron jobs
- [ ] Update Vapi webhooks
- [ ] Migrate test lead through full flow
- [ ] Monitor logs for 24 hours

### Phase 4: Production Cutover (Week 4)
- [ ] Migrate all active leads
- [ ] Run parallel for 48 hours (v1 + v2)
- [ ] Compare decision quality
- [ ] Full cutover to v2
- [ ] Deprecate v1 code

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Performance** | | |
| Brain API response | < 2s (p95) | `/decide` endpoint latency |
| End-to-end SMS reply | < 5s | Webhook → Twilio send |
| Memory search | < 500ms | Embedding similarity query |
| **Reliability** | | |
| System uptime | > 99.5% | Uptime monitoring |
| Brain API failures | < 0.1% | Error rate (with fallback) |
| Data loss | 0% | All messages in Sarah DB |
| **Intelligence** | | |
| Decision accuracy | > 95% | Owner review of decisions |
| Learning improvement | +10% conversion in 60d | Win rate over time |
| Similar conversation relevance | > 80% | Manual review of matches |

---

## 10. Open Questions & Decisions

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Deploy Brain on same VPS or separate? | ✅ Same VPS | Lower latency, simpler ops for MVP |
| 2 | Brain storage: Own DB or Sarah DB? | ✅ Hybrid | brain.db for speed, Sarah DB for persistence |
| 3 | Learning frequency: Real-time or nightly? | ✅ Nightly batch | Less API load, sufficient for learning |
| 4 | Voice: Keep Make.com or Python? | ✅ Migrate to Python | Single codebase, easier debugging |
| 5 | Fallback model if Claude fails? | ✅ GPT-4o-mini | OpenClaw handles automatically |

---

## 11. Comparison: v1.0 vs v2.0

| Aspect | v1.0 (Current) | v2.0 (OpenClaw Brain) |
|--------|----------------|----------------------|
| **Decision Engine** | Hardcoded rules in Python | OpenClaw agent runtime with AI tools |
| **Memory/Learning** | Basic intent tracking | Vector embeddings + hybrid search |
| **Multi-model** | OpenAI only | Claude, GPT, Gemini with failover |
| **Context Management** | Manual string building | Automatic compaction, token budget |
| **Voice Integration** | Make.com scenarios | Python vapi_handler.py |
| **Pattern Matching** | None | Similarity search in past conversations |
| **Session Management** | Basic (Sarah DB) | Advanced (OpenClaw sessions + brain.db) |
| **Code Maintainability** | Custom logic scattered | Clean separation (Python I/O, TS brain) |
| **Future Channels** | Requires Python coding | Reuse Brain API (add handler only) |
| **Learning Capability** | Manual rules updates | Automatic pattern learning |

---

## 12. Next Steps

**For Review:**
1. Read this document in full
2. Review `docs/FILE_STRUCTURE.md` for detailed file organization
3. Approve or request changes to architecture

**After Approval:**
1. Proceed with Phase 1 extraction
2. Follow migration checklist in FILE_STRUCTURE.md
3. Weekly progress reviews

---

**Status:** 🔴 PENDING ARCHITECTURAL REVIEW  
**Review Required By:** Shiva (Product Owner)  
**Questions/Feedback:** See GitHub issues or direct communication

---

*This is a living document. Update as architecture evolves.*
