# Sarah AI - System Architecture

**Version:** 2.0  
**Created:** 2026-03-15  
**Updated:** 2026-03-16 (OpenClaw Brain Integration)  
**Authors:** Shiva (Product), Bo (Architecture)  
**Status:** Architecture Review - Pending Approval

---

## 1. Vision

Sarah is an **autonomous AI Sales Agent** that lives inside a business. She handles inbound/outbound communication across SMS, Voice, and Email — making intelligent decisions about when, how, and what to say to each lead.

Unlike a chatbot that just responds, Sarah:
- **Orchestrates** across channels (decides SMS vs call vs email)
- **Learns** from each business over 1-2 months
- **Adapts** her communication style per lead
- **Reports** to the business owner through familiar channels

**Architecture Philosophy:** Sarah is built as a **hybrid system**:
- **Python Shell** (outer layer): Proven channel handlers (SMS/Twilio, Voice/Vapi), scheduling, CRM integration
- **TypeScript Brain** (core): Extracted OpenClaw components for intelligent decision-making, memory, and learning

This approach leverages OpenClaw's production-tested AI agent runtime while keeping Sarah's specialized sales logic and multi-lead management intact.

---

## 2. Design Principles

| Principle | Meaning |
|-----------|---------|
| **CRM-Agnostic** | Works with Zoho today, Salesforce/HubSpot tomorrow |
| **Channel-Agnostic** | SMS, Voice, Email, WhatsApp — same brain |
| **Living Memory** | Learns contact preferences, sales patterns, personas |
| **Owner-Accessible** | Business owner talks to Sarah via Telegram/iMessage |
| **Auditable** | Every decision logged, every message tracked |

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
│                                                                          │
│                         SARAH ORCHESTRATION LAYER                        │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │  Decision      │  │  Memory &      │  │  Learning      │             │
│  │  Engine        │  │  Context       │  │  Module        │             │
│  │                │  │                │  │                │             │
│  │ • When to act  │  │ • Lead history │  │ • Best times   │             │
│  │ • Which channel│  │ • Preferences  │  │ • Persona fit  │             │
│  │ • What to say  │  │ • Sentiment    │  │ • Win patterns │             │
│  │ • Escalate?    │  │ • Status       │  │ • Loss reasons │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  SMS Channel  │          │ Voice Channel │          │ Email Channel │
│   (Twilio)    │          │    (Vapi)     │          │  (SendGrid)   │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                    │
│                                                                          │
│  ┌─────────────────────────┐       ┌─────────────────────────┐          │
│  │      SARAH DB           │◄─────►│      CRM ADAPTER        │          │
│  │   (Source of Truth)     │ Sync  │   (Zoho / Salesforce)   │          │
│  │                         │       │                         │          │
│  │ • Conversations         │       │ • Lead/Contact records  │          │
│  │ • Message logs          │       │ • Deal status           │          │
│  │ • Decision history      │       │ • Notes (from Sarah)    │          │
│  │ • Learning data         │       │ • Calendar/Tasks        │          │
│  └─────────────────────────┘       └─────────────────────────┘          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Details

### 4.1 Orchestration Layer

The brain of Sarah. Runs on a schedule (cron) AND reactively (webhooks).

**Decision Engine:**
```
Input:
  - Lead context (status, last interaction, sentiment)
  - Time since last contact
  - Lead's stated preferences ("call me next Tuesday")
  - Channel availability

Output:
  - Action: WAIT | SMS | CALL | EMAIL | ESCALATE | STOP
  - Content: AI-generated message
  - Timing: Now | Scheduled
```

**Decision Rules (configurable per business):**
| Scenario | Decision |
|----------|----------|
| Lead replied positively | Mark HOT_LEAD, notify owner |
| No response 30 min | Send SMS follow-up |
| No response 24 hrs | Send different angle SMS |
| No response 72 hrs | Try voice call |
| Lead said "call me at 3pm" | Schedule call, don't SMS |
| Lead said "not interested" | Mark CLOSED_LOST, stop all |
| Lead booked appointment | Confirm, stop follow-ups |
| High-value lead detected | Alert owner immediately |

**Memory & Context:**
- Full conversation history (all channels, all messages)
- Lead profile (name, email, company, preferences)
- Sentiment trajectory (getting warmer? colder?)
- Best contact window (learned over time)
- Channel preference (responds to SMS but ignores email)

**Learning Module:**
- Tracks which approaches convert
- Learns optimal timing per lead segment
- Identifies winning message patterns
- Adjusts persona/tone based on lead type

---

### 4.2 Channel Adapters

Each channel is a plugin. Same interface, different implementation.

**Channel Interface:**
```python
class ChannelAdapter:
    def send(self, lead_id, message, metadata) -> SendResult
    def receive(self, webhook_data) -> InboundMessage
    def get_status(self, message_id) -> DeliveryStatus
```

**Implemented Channels:**
| Channel | Provider | Inbound | Outbound | Status |
|---------|----------|---------|----------|--------|
| SMS | Twilio | ✅ | ✅ | Live |
| Voice | Vapi | ✅ | ✅ | Live (separate) |
| Email | SendGrid | ❌ | ❌ | Planned |
| WhatsApp | Twilio | ❌ | ❌ | Planned |

---

### 4.3 Data Layer

**Sarah DB (Standalone PostgreSQL/SQLite):**

```
┌─────────────────────────────────────────────────────────────┐
│                         SARAH DB                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  leads                     conversations                    │
│  ├─ lead_id (PK)          ├─ conversation_id (PK)          │
│  ├─ external_crm_id       ├─ lead_id (FK)                  │
│  ├─ name                  ├─ channel                       │
│  ├─ email                 ├─ status (active/closed)        │
│  ├─ phone                 ├─ intent                        │
│  ├─ company               ├─ sentiment                     │
│  ├─ source                ├─ summary                       │
│  ├─ preferences (JSON)    ├─ last_interaction_at           │
│  ├─ best_contact_time     └─ created_at                    │
│  ├─ channel_preference                                      │
│  └─ created_at            messages                          │
│                           ├─ message_id (PK)               │
│  decisions                ├─ conversation_id (FK)          │
│  ├─ decision_id (PK)      ├─ direction (in/out)            │
│  ├─ lead_id (FK)          ├─ channel                       │
│  ├─ action_taken          ├─ body                          │
│  ├─ reasoning             ├─ metadata (JSON)               │
│  ├─ outcome               └─ created_at                    │
│  └─ created_at                                              │
│                           learnings                         │
│                           ├─ learning_id (PK)              │
│                           ├─ pattern_type                  │
│                           ├─ pattern_data (JSON)           │
│                           ├─ confidence                    │
│                           └─ created_at                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**CRM Adapter (Bidirectional Sync):**

```
Sarah DB ←→ CRM Adapter ←→ Zoho CRM
                │
                ├─ On new lead in CRM → Create in Sarah DB
                ├─ On message sent → Write note to CRM
                ├─ On status change → Update CRM deal stage
                ├─ On booking → Create CRM task/event
                └─ On CRM update → Sync to Sarah DB
```

**Adapter Interface:**
```python
class CRMAdapter:
    def sync_lead(self, sarah_lead) -> crm_id
    def fetch_lead(self, crm_id) -> sarah_lead
    def write_note(self, crm_id, note) -> success
    def create_task(self, crm_id, task) -> task_id
    def get_changes_since(self, timestamp) -> changes[]
```

**Implemented CRMs:**
| CRM | Status | Notes |
|-----|--------|-------|
| Zoho CRM | 🟡 Partial | Read works, write via Make.com |
| Salesforce | ❌ Planned | |
| HubSpot | ❌ Planned | |
| GoHighLevel | ❌ Planned | |

---

### 4.4 Owner Interface

The business owner communicates with Sarah like they would with an employee.

**Channels:**
- Telegram (primary)
- iMessage (via OpenClaw gateway)
- Email (fallback)

**Capabilities:**
| Owner Says | Sarah Does |
|------------|------------|
| "How's lead John Doe?" | Pulls context, summarizes status |
| "Call him now" | Triggers immediate outbound call |
| "Stop following up with ABC Corp" | Marks lead as closed, stops automation |
| "What's my pipeline today?" | Summarizes active leads, next actions |
| "Change follow-up to 48 hours" | Updates strategy for that lead |

**Alerts to Owner:**
- Hot lead detected (booking requested, high intent)
- Handoff requested ("talk to a human")
- Negative sentiment spike
- Lead went cold after being hot
- Daily/weekly summary (configurable)

---

## 5. Data Flow Examples

### 5.1 Inbound SMS

```
1. Lead sends SMS to Twilio number
2. Twilio webhook → Sarah SMS Adapter
3. Adapter parses → creates InboundMessage
4. Orchestrator:
   a. Fetches lead context from Sarah DB
   b. Adds message to conversation history
   c. Runs Decision Engine:
      - Analyze sentiment
      - Extract info (name, email, intent)
      - Decide response
   d. Generates AI reply
   e. Sends via SMS Adapter
   f. Logs decision + message
   g. Updates lead profile
5. CRM Adapter syncs note to Zoho
```

### 5.2 Inbound Voice Call

```
1. Lead calls Vapi number
2. Vapi webhook → Make.com scenario
3. Make.com:
   a. Calls Sarah API: GET /context/{phone}
   b. Returns lead context to Vapi
4. Vapi conducts conversation
5. Call ends → Make.com:
   a. Sends call summary to Sarah API
   b. Sarah logs to conversation history
   c. Updates lead status/sentiment
   d. Writes note to Zoho CRM
6. Orchestrator evaluates next action
```

### 5.3 Scheduled Follow-up

```
1. Cron triggers every 5 minutes
2. Orchestrator queries: leads needing action
3. For each lead:
   a. Check last_interaction_at vs strategy rules
   b. Decision Engine decides action
   c. If action = SMS:
      - Generate contextual message
      - Send via SMS Adapter
      - Log decision + message
   d. If action = CALL:
      - Trigger outbound via Vapi
   e. If action = ESCALATE:
      - Alert owner via Telegram
4. Update all lead statuses
```

---

## 6. Configuration

Each business instance of Sarah has a config file:

```yaml
# sarah_config.yaml

business:
  name: "Kalkia Évolution IA"
  timezone: "America/Toronto"
  owner_channel: "telegram"
  owner_id: "8290509439"

crm:
  provider: "zoho"
  api_key: "${ZOHO_API_KEY}"
  sync_interval_minutes: 5

channels:
  sms:
    provider: "twilio"
    phone_number: "+15551234567"
  voice:
    provider: "vapi"
    assistant_id: "xxx"
  email:
    enabled: false

strategy:
  default_followup_minutes: [30, 1440, 4320]  # 30min, 24hr, 72hr
  max_followups: 3
  business_hours:
    start: "09:00"
    end: "18:00"
    days: ["Mon", "Tue", "Wed", "Thu", "Fri"]
  
escalation:
  hot_lead_keywords: ["buy", "ready", "sign up", "pricing"]
  handoff_keywords: ["human", "manager", "call me"]

learning:
  enabled: true
  training_period_days: 60
  min_conversations_to_learn: 50
```

---

## 7. Deployment Architecture

### 7.1 Per-Client Deployment

Each client (Kalkia, Alain, future clients) gets:

```
┌─────────────────────────────────────────┐
│           CLIENT VPS / CONTAINER        │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         Sarah Instance          │   │
│  │                                 │   │
│  │  • Flask App (webhooks)         │   │
│  │  • Cron Worker (scheduler)      │   │
│  │  • Redis (job queue)            │   │
│  │  • SQLite/PostgreSQL (Sarah DB) │   │
│  │  • Config (business-specific)   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Connected to:                          │
│  • Client's Twilio account              │
│  • Client's Vapi account                │
│  • Client's Zoho CRM                    │
│  • Owner's Telegram                     │
│                                         │
└─────────────────────────────────────────┘
```

### 7.2 Multi-Tenant (Future)

```
┌─────────────────────────────────────────┐
│         SARAH CLOUD (SaaS)              │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Shared Infrastructure          │   │
│  │   • API Gateway                  │   │
│  │   • Orchestration Service        │   │
│  │   • Channel Adapters             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Client A │ │Client B │ │Client C │   │
│  │  Data   │ │  Data   │ │  Data   │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 8. Migration Path (Current → Target)

### Phase 1: Connect Voice to Sarah DB (Mar 16-18)
- Update Make.com to write to Sarah DB
- Keep Zoho CRM write (dual-write)
- Voice calls now visible in Sarah's conversation history

### Phase 2: Unified Orchestration (Mar 19-21)
- Single cron worker manages SMS + Voice follow-ups
- Decision engine considers all channel history
- Owner alerts via Telegram

### Phase 3: CRM Abstraction (Week 2)
- Build CRM Adapter interface
- Implement Zoho Adapter properly
- Bidirectional sync working

### Phase 4: Learning Module (Month 1-2)
- Collect conversion data
- Train on patterns
- Auto-adjust timing and messaging

---

## 9. Open Questions

| # | Question | Decision Needed By |
|---|----------|-------------------|
| 1 | Host Sarah DB on same VPS or separate? | Mar 16 |
| 2 | Use existing Sarah DB schema or redesign? | Mar 16 |
| 3 | Voice outbound — Vapi supports this? | Mar 17 |
| 4 | Owner interface — new Telegram bot or via OpenClaw? | Mar 18 |

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Lead response time | < 5 min |
| Follow-up completion rate | 100% |
| Channel unification | All in one view |
| Owner can query Sarah | Yes |
| Learning improves conversion | +10% in 60 days |

---

*This is a living document. Update as architecture evolves.*
