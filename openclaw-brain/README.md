# OpenClaw Brain - Sarah AI Decision Engine

**Status:** 🔴 Architecture Phase - Not Yet Implemented

This directory contains extracted OpenClaw components that power Sarah's intelligent decision-making.

## What This Is

Sarah's "brain" - extracted from [OpenClaw](https://github.com/openclaw/openclaw) - handles:
- **Agent Runtime**: Multi-model AI execution (Claude, GPT, Gemini)
- **Memory System**: Vector embeddings, similarity search, pattern matching
- **Session Management**: Conversation tracking, context windows, compaction
- **Decision Tools**: Sarah-specific business logic as AI-callable functions

## Architecture

```
Sarah Python Layer (Port 5000)
         ↓
    HTTP POST /decide
         ↓
OpenClaw Brain (Port 3000) ← THIS DIRECTORY
         ↓
  brain.db (SQLite)
```

## Directory Structure

```
openclaw-brain/
├── src/
│   ├── agents/           # ✅ Extract from OpenClaw
│   │   ├── pi-embedded-runner.ts
│   │   ├── pi-embedded-subscribe.ts
│   │   ├── pi-tools.ts
│   │   └── ...
│   ├── memory/           # ✅ Extract from OpenClaw
│   │   ├── manager.ts
│   │   ├── embeddings.ts
│   │   ├── search-manager.ts
│   │   └── ...
│   ├── sessions/         # ✅ Extract from OpenClaw
│   │   ├── session-id.ts
│   │   └── transcript-events.ts
│   ├── sarah-brain-api.ts  # 🆕 NEW - HTTP API wrapper
│   └── utils.ts          # ✅ Extract from OpenClaw
├── tools/                # 🆕 NEW - Sarah-specific tools
│   ├── decide_next_action.ts
│   ├── search_similar_conversations.ts
│   └── ...
├── config/
│   └── sarah-agent-config.json
├── data/
│   └── brain.db          # SQLite database (gitignored)
└── scripts/
    └── extract-from-openclaw.sh  # Extraction helper
```

## Installation (After Extraction)

```bash
cd openclaw-brain
npm install
cp .env.example .env
# Edit .env with your API keys
npm run dev
```

## API Endpoints

### POST /decide
Main decision endpoint - receives lead context, returns action decision.

**Request:**
```json
{
  "lead_context": {
    "customer_id": 123,
    "phone": "+15551234567",
    "intent": "WAITING_FOR_ANSWER",
    "sentiment": "neutral",
    "conversation_history": [...]
  },
  "user_message": "Hi, I'm interested in...",
  "channel": "sms"
}
```

**Response:**
```json
{
  "action": "SMS",
  "message": "Thanks for reaching out! Would you like to schedule...",
  "reasoning": "Lead showing interest, asking qualifying question",
  "new_intent": "ENGAGED",
  "sentiment": "positive"
}
```

### POST /learn
Index conversation for learning (called by nightly_learning.py).

### GET /health
Health check endpoint.

## Next Steps

1. **Review Architecture** - See `../docs/ARCHITECTURE_v2_OPENCLAW.md`
2. **Extract Files** - See `../docs/OPENCLAW_EXTRACTION_GUIDE.md` (to be created)
3. **Build Tools** - Implement Sarah-specific decision logic
4. **Test Standalone** - Verify Brain API works independently
5. **Integrate** - Connect to Python layer via sarah_orchestrator.py

## Status

- [ ] Files extracted from OpenClaw
- [ ] HTTP API wrapper implemented
- [ ] Sarah tools created
- [ ] Tested standalone
- [ ] Integrated with Python layer
- [ ] Deployed to production

## License

Extracted components maintain OpenClaw's MIT license.
Sarah-specific tools (tools/) are proprietary.
