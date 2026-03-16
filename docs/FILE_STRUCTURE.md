# Sarah AI - File Structure with OpenClaw Brain Integration

**Version:** 2.0  
**Updated:** 2026-03-16  
**Status:** Architectural Review - Pending Approval

---

## Overview

Sarah is built as a **hybrid architecture**:
- **Python Shell** (outer layer): Handles channels (SMS, Voice, Email), CRM integration, scheduling
- **TypeScript Brain** (core): OpenClaw-extracted components for intelligent decision-making, memory, and learning

---

## Complete File Structure

```
Follow-up_agent/
│
├── README.md                           # Project overview
├── requirements.txt                    # Python dependencies
├── .env                                # Environment variables
├── .gitignore
├── docker-compose.yml                  # Multi-container setup (Flask + Brain + Redis)
├── Dockerfile                          # Python container
│
├── docs/                               # Documentation
│   ├── ARCHITECTURE.md                 # ✨ UPDATED - OpenClaw Brain architecture
│   ├── FILE_STRUCTURE.md              # 🆕 THIS FILE
│   ├── TECH_SPEC_FOR_DEVELOPER.md     # Technical specification
│   ├── AGENTS.md                       # Development guidelines
│   ├── API_REFERENCE.md               # Sarah DB API reference
│   ├── ENDPOINT_REFERENCE.md          # Detailed endpoints
│   ├── DEPLOYMENT_SOP.md              # Deployment procedures
│   └── OPENCLAW_EXTRACTION_GUIDE.md   # 🆕 How to extract from OpenClaw repo
│
├── app.py                              # 🔄 MODIFIED - Flask app using orchestrator
├── main.py                             # DEPRECATED - will remove after migration
├── config.py                           # Configuration (currently empty)
├── utils.py                            # Logging helpers
│
├── sarah_db_client.py                  # Sarah DB API client (no changes)
├── sarah_orchestrator.py              # 🆕 NEW - Coordinates Python + Brain
├── vapi_handler.py                     # 🆕 NEW - Voice webhook handler (replaces Make.com)
├── nightly_learning.py                 # 🆕 NEW - Batch learning job
│
├── cron_worker.py                      # 🔄 MODIFIED - Simplified to use orchestrator
├── tasks.py                            # RQ task definitions (keep for now)
├── followup_strategy.json              # Follow-up timing rules
│
├── openclaw-brain/                     # 🆕 NEW - Extracted OpenClaw components
│   ├── package.json                    # Node.js dependencies
│   ├── tsconfig.json                   # TypeScript configuration
│   ├── .gitignore
│   ├── README.md                       # Brain-specific documentation
│   │
│   ├── src/                            # Core OpenClaw code (extracted)
│   │   ├── agents/                     # Agent runtime
│   │   │   ├── pi-embedded-runner.ts   # ✅ Core agent execution
│   │   │   ├── pi-embedded-subscribe.ts # ✅ Streaming handler
│   │   │   ├── pi-tools.ts             # ✅ Tool execution framework
│   │   │   ├── system-prompt.ts        # ✅ Prompt building
│   │   │   ├── model-fallback.ts       # ✅ Multi-model failover
│   │   │   ├── usage.ts                # ✅ Token tracking
│   │   │   ├── compaction.ts           # ✅ Context window management
│   │   │   └── context.ts              # ✅ Context management
│   │   │
│   │   ├── memory/                     # Memory & learning system
│   │   │   ├── manager.ts              # ✅ Memory index manager
│   │   │   ├── embeddings.ts           # ✅ Vector embeddings
│   │   │   ├── search-manager.ts       # ✅ Search interface
│   │   │   ├── sqlite-vec.ts           # ✅ SQLite vector extension
│   │   │   ├── hybrid.ts               # ✅ Hybrid search (vector + keyword)
│   │   │   └── types.ts                # ✅ Type definitions
│   │   │
│   │   ├── sessions/                   # Session management
│   │   │   ├── session-id.ts           # ✅ Session identification
│   │   │   ├── transcript-events.ts    # ✅ Conversation tracking
│   │   │   └── session-key-utils.ts    # ✅ Session utilities
│   │   │
│   │   ├── infra/                      # Infrastructure
│   │   │   ├── logger.ts               # ✅ Logging utilities
│   │   │   └── config.ts               # ✅ Configuration loader
│   │   │
│   │   ├── types/                      # Shared TypeScript types
│   │   │   └── index.ts                # ✅ Type exports
│   │   │
│   │   ├── utils.ts                    # ✅ General utilities
│   │   └── sarah-brain-api.ts          # 🆕 NEW - HTTP API wrapper
│   │
│   ├── tools/                          # 🆕 Sarah-specific tools
│   │   ├── decide_next_action.ts       # Decision engine logic
│   │   ├── search_similar_conversations.ts # Pattern matching
│   │   ├── detect_intent.ts            # Intent classification
│   │   ├── extract_contact_info.ts     # Name/email extraction
│   │   ├── analyze_sentiment.ts        # Sentiment analysis
│   │   └── index.ts                    # Tool registry
│   │
│   ├── config/                         # Brain configuration
│   │   ├── sarah-agent-config.json     # Agent behavior settings
│   │   └── models.json                 # Model provider configs
│   │
│   ├── data/                           # Runtime data (gitignored)
│   │   ├── brain.db                    # SQLite database (sessions + memory)
│   │   └── logs/                       # Brain-specific logs
│   │
│   └── scripts/                        # Utility scripts
│       ├── extract-from-openclaw.sh    # Extraction helper
│       └── test-brain-api.sh           # API testing script
│
└── voice-ai/                           # Voice integration docs (keep for reference)
    ├── README.md                       # Voice architecture (update with Python migration)
    └── make-scenario/                  # DEPRECATED - Replaced by vapi_handler.py
        ├── incoming-call.json
        └── call-ended.json
```

---

## File Descriptions

### **Root Level (Python Layer)**

#### **sarah_orchestrator.py** 🆕 NEW
```python
# Purpose: Central coordinator between Python channels and TypeScript Brain
# Responsibilities:
#   - Fetch context from Sarah DB
#   - Call OpenClaw Brain API for decisions
#   - Execute actions (send SMS, trigger calls, notify owner)
#   - Log to Sarah DB
#   - Handle Brain API failures with fallback logic
```

#### **vapi_handler.py** 🆕 NEW
```python
# Purpose: Handle Vapi voice webhooks (replaces Make.com)
# Endpoints:
#   - POST /vapi/call-started - Return lead context to Vapi
#   - POST /vapi/call-ended - Process transcript and schedule follow-up
# Integrates with: sarah_orchestrator, sarah_db_client, OpenClaw Brain
```

#### **nightly_learning.py** 🆕 NEW
```python
# Purpose: Nightly batch job to index closed conversations
# Schedule: Daily at 2 AM (cron: 0 2 * * *)
# Logic:
#   1. Fetch all CLOSED_WON/HOT_LEAD conversations from Sarah DB (last 24h)
#   2. Call OpenClaw Brain /learn endpoint to index messages
#   3. Prune old sessions from brain.db
#   4. Generate learning report
```

#### **app.py** 🔄 MODIFIED
```python
# Changes:
#   - Import sarah_orchestrator
#   - Replace inline decision logic with orchestrator.handle_inbound_sms()
#   - Keep Twilio webhook handling
#   - Remove OpenAI function calling code (moved to Brain)
```

#### **cron_worker.py** 🔄 MODIFIED
```python
# Changes:
#   - Simplified to call orchestrator.check_followups_due()
#   - Remove Sarah DB iteration logic (Brain decides per-lead)
#   - Keep cron scheduling logic
```

---

### **openclaw-brain/ (TypeScript Layer)**

#### **src/sarah-brain-api.ts** 🆕 NEW
```typescript
// Purpose: HTTP API exposing OpenClaw Brain to Python layer
// Endpoints:
//   - POST /decide - Main decision endpoint
//     Input: { lead_context, user_message, channel }
//     Output: { action, message, reasoning, new_intent, sentiment }
//   
//   - POST /learn - Index conversation for learning
//     Input: { conversation_id, outcome, messages[] }
//     Output: { indexed: number }
//   
//   - GET /health - Health check
//     Output: { status: "ok", uptime: number }
//   
//   - GET /memory/search - Search similar conversations
//     Input: { query, lead_type, outcome_filter }
//     Output: { results: [...] }
```

#### **tools/decide_next_action.ts** 🆕 NEW
```typescript
// Purpose: Core decision logic (maps to ARCHITECTURE.md Section 4.1)
// Tool definition for OpenAI function calling
// Parameters:
//   - lead_state: object (customer_id, name, phone, intent, sentiment)
//   - time_since_last_interaction: number (seconds)
//   - conversation_summary: string
//   - channel_history: object (preferred_channel, response_rates)
// 
// Returns:
//   - action: "WAIT" | "SMS" | "CALL" | "EMAIL" | "ESCALATE" | "STOP"
//   - message: string (if action=SMS/EMAIL)
//   - reasoning: string
//   - schedule_delay: number (minutes, if action=WAIT)
```

#### **tools/search_similar_conversations.ts** 🆕 NEW
```typescript
// Purpose: Leverage memory system to find similar past conversations
// Uses: OpenClaw's MemorySearchManager for hybrid search
// Logic:
//   1. Query memory with lead's situation
//   2. Filter by outcome (won/lost/any)
//   3. Return top 5 similar conversations with similarity scores
//   4. AI uses these to inform decision-making
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     INBOUND MESSAGE                         │
│         (SMS from Twilio / Voice from Vapi)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  app.py / vapi_handler.py (Python - Port 5000/5001)        │
│  • Receives webhook                                         │
│  • Validates request                                        │
│  • Extracts: from_phone, body, channel                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  sarah_orchestrator.py (Python Coordinator)                │
│                                                             │
│  1. Fetch Context                                          │
│     context = sarah_db.get_context(from_phone)             │
│                                                             │
│  2. Call Brain                                             │
│     decision = brain_api.post('/decide', {                 │
│         lead_context: context,                             │
│         user_message: body,                                │
│         channel: channel                                   │
│     })                                                      │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP localhost:3000
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  sarah-brain-api.ts (TypeScript - Port 3000)               │
│                                                             │
│  • Builds system prompt with lead context                  │
│  • Calls runEmbeddedPiAgent() with Sarah tools            │
│  • Agent decides: WAIT | SMS | CALL | EMAIL | ESCALATE    │
│  • Returns decision to Python layer                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  OpenClaw Agent Runtime (pi-embedded-runner.ts)            │
│                                                             │
│  • Loads conversation history from brain.db                │
│  • Executes AI model (Claude, GPT, etc.)                  │
│  • Calls tools: decide_next_action, search_similar, etc.  │
│  • Manages token budget, retries, failover                │
│  • Stores session back to brain.db                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Memory System (memory/manager.ts)                         │
│                                                             │
│  • Searches brain.db for similar conversations             │
│  • Vector similarity + keyword matching                    │
│  • Returns patterns from successful past interactions      │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼ (Returns decision)
┌─────────────────────────────────────────────────────────────┐
│  sarah_orchestrator.py (Execute Decision)                  │
│                                                             │
│  if decision.action == "SMS":                              │
│      twilio.send_sms(from_phone, decision.message)         │
│  elif decision.action == "CALL":                           │
│      vapi.trigger_outbound_call(from_phone)                │
│  elif decision.action == "ESCALATE":                       │
│      telegram.notify_owner(context, decision.reason)       │
│                                                             │
│  # Log everything to Sarah DB                              │
│  sarah_db.log_message(...)                                 │
│  sarah_db.update_conversation(...)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Storage Architecture (Hybrid Approach)

### **Short-term Storage (brain.db - SQLite)**

Located: `openclaw-brain/data/brain.db`

**Tables:**
```sql
-- Active conversation sessions (last 50 messages per lead)
sessions (
    session_key TEXT PRIMARY KEY,      -- phone number
    customer_id INTEGER,
    last_interaction TIMESTAMP,
    message_count INTEGER,
    created_at TIMESTAMP
)

-- Recent messages (pruned after 7 days)
messages (
    message_id TEXT PRIMARY KEY,
    session_key TEXT,
    role TEXT,                         -- 'user' | 'assistant'
    content TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (session_key) REFERENCES sessions(session_key)
)

-- Vector embeddings for similarity search
embeddings (
    embedding_id TEXT PRIMARY KEY,
    text TEXT,
    vector BLOB,                       -- sqlite-vec format
    metadata JSON,                     -- { outcome, lead_type, sentiment }
    indexed_at TIMESTAMP
)
```

**Retention:**
- Sessions: Keep active conversations + 7 days after last message
- Embeddings: Keep indefinitely (learning data)
- Prune nightly via `nightly_learning.py`

### **Long-term Storage (Sarah DB - AWS API)**

Accessed via: `sarah_db_client.py` → AWS Lambda

**Responsibilities:**
- Full conversation history (all messages, forever)
- Customer/Lead records
- Decision logs
- CRM integration data
- Closed conversation outcomes

**Sync Strategy:**
- Python layer writes to Sarah DB immediately after each interaction
- Nightly job reads closed conversations → indexes into brain.db
- Brain.db is ephemeral cache, Sarah DB is source of truth

---

## Environment Variables

### **Python Layer (.env)**
```bash
# Existing
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
CORE_API_KEY=your_api_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
AGENT_NAME=Sarah

# New
OPENCLAW_BRAIN_URL=http://localhost:3000
VAPI_API_KEY=your_vapi_key
VAPI_PHONE_NUMBER=your_vapi_number
TELEGRAM_BOT_TOKEN=your_bot_token  # For owner notifications
OWNER_TELEGRAM_ID=8290509439
```

### **TypeScript Brain (openclaw-brain/.env)**
```bash
# Model providers
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Default model
DEFAULT_MODEL=anthropic/claude-sonnet-4

# Database
DATABASE_PATH=./data/brain.db

# API settings
PORT=3000
LOG_LEVEL=info
```

---

## Deployment Configuration

### **docker-compose.yml** (Updated)

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
    command: gunicorn -w 4 -b 0.0.0.0:5000 app:app

  openclaw-brain:
    build: ./openclaw-brain
    ports:
      - "3000:3000"
    volumes:
      - ./openclaw-brain/data:/app/data
    environment:
      - NODE_ENV=production
      - DATABASE_PATH=/app/data/brain.db
    command: npm start

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

### **Cron Jobs**

```bash
# On VPS (crontab -e)

# Follow-up check every 5 minutes
*/5 * * * * cd /home/ubuntu/Follow-up_agent && python3 cron_worker.py >> /var/log/sarah/cron.log 2>&1

# Nightly learning at 2 AM
0 2 * * * cd /home/ubuntu/Follow-up_agent && python3 nightly_learning.py >> /var/log/sarah/learning.log 2>&1

# Daily backup of brain.db at 3 AM
0 3 * * * cp /home/ubuntu/Follow-up_agent/openclaw-brain/data/brain.db /home/ubuntu/backups/brain-$(date +\%Y\%m\%d).db
```

---

## Migration Checklist

### **Phase 1: Setup OpenClaw Brain** ✅
- [ ] Create `openclaw-brain/` directory structure
- [ ] Copy files from `/tmp/openclaw/` (use extraction guide)
- [ ] Install dependencies (`npm install`)
- [ ] Create `sarah-brain-api.ts`
- [ ] Create Sarah-specific tools
- [ ] Test Brain API standalone (`npm run dev`)

### **Phase 2: Python Integration** ✅
- [ ] Create `sarah_orchestrator.py`
- [ ] Create `vapi_handler.py`
- [ ] Create `nightly_learning.py`
- [ ] Update `app.py` to use orchestrator
- [ ] Update `cron_worker.py` to use orchestrator
- [ ] Test locally (both services running)

### **Phase 3: Deploy** ✅
- [ ] Deploy to VPS (Docker or direct)
- [ ] Configure systemd services
- [ ] Setup cron jobs
- [ ] Update Vapi webhooks to point to `vapi_handler.py`
- [ ] Migrate one test lead through full flow
- [ ] Monitor logs for 24 hours

### **Phase 4: Cleanup** ✅
- [ ] Remove `main.py` (deprecated)
- [ ] Remove `voice-ai/make-scenario/` (replaced)
- [ ] Archive old implementation docs
- [ ] Update README.md with new architecture
- [ ] Document rollback procedure

---

## Success Metrics

**Performance:**
- Brain API response time < 2s (95th percentile)
- End-to-end SMS reply < 5s (webhook → reply sent)
- Memory search < 500ms

**Reliability:**
- Uptime > 99.5%
- Failed Brain API calls < 0.1% (with fallback)
- Zero data loss (all messages logged to Sarah DB)

**Learning:**
- Memory index grows with closed conversations
- Similar conversation search returns relevant results
- Decision quality improves over 60 days (measured by conversion rate)

---

**Review Status:** 🔴 Pending Approval  
**Next Step:** Review this structure, then proceed to code implementation  
**Questions:** See `docs/ARCHITECTURE.md` for architectural decisions
