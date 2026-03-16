# OpenClaw Extraction Guide

**Purpose:** Step-by-step guide to extract OpenClaw brain components  
**Target:** `openclaw-brain/` directory in Sarah project  
**Source:** `/tmp/openclaw/` (cloned OpenClaw repository)

---

## Prerequisites

```bash
# Verify OpenClaw repo is cloned
ls /tmp/openclaw/

# Expected output: should see src/, packages/, README.md, etc.
```

---

## Extraction Steps

### Step 1: Core Agent Runtime

Copy these files from OpenClaw to Sarah's `openclaw-brain/src/agents/`:

```bash
SOURCE=/tmp/openclaw/src/agents
DEST="/mnt/c/Drive D/Projects/Antigravity/Follow-up_agent/openclaw-brain/src/agents"

# Core agent execution
cp $SOURCE/pi-embedded-runner.ts $DEST/
cp $SOURCE/pi-embedded-subscribe.ts $DEST/
cp $SOURCE/pi-embedded.ts $DEST/

# Tool execution framework
cp $SOURCE/pi-tools.ts $DEST/
cp $SOURCE/pi-tool-definition-adapter.ts $DEST/

# System prompts
cp $SOURCE/system-prompt.ts $DEST/
cp $SOURCE/system-prompt-params.ts $DEST/

# Model failover & multi-provider support
cp $SOURCE/model-fallback.ts $DEST/
cp $SOURCE/model-selection.ts $DEST/
cp $SOURCE/model-catalog.ts $DEST/

# Token tracking
cp $SOURCE/usage.ts $DEST/

# Context management
cp $SOURCE/compaction.ts $DEST/
cp $SOURCE/context.ts $DEST/
cp $SOURCE/context-window-guard.ts $DEST/

# Helper modules
cp $SOURCE/content-blocks.ts $DEST/
cp $SOURCE/pi-embedded-helpers.ts $DEST/
cp $SOURCE/pi-embedded-payloads.ts $DEST/
```

### Step 2: Memory System

Copy these files to `openclaw-brain/src/memory/`:

```bash
SOURCE=/tmp/openclaw/src/memory
DEST="/mnt/c/Drive D/Projects/Antigravity/Follow-up_agent/openclaw-brain/src/memory"

# Core memory management
cp $SOURCE/manager.ts $DEST/
cp $SOURCE/search-manager.ts $DEST/
cp $SOURCE/index.ts $DEST/
cp $SOURCE/types.ts $DEST/

# Embeddings (vector generation)
cp $SOURCE/embeddings.ts $DEST/
cp $SOURCE/embeddings-openai.ts $DEST/
cp $SOURCE/embeddings-gemini.ts $DEST/
cp $SOURCE/embeddings-voyage.ts $DEST/
cp $SOURCE/embeddings-ollama.ts $DEST/

# SQLite vector extension
cp $SOURCE/sqlite-vec.ts $DEST/
cp $SOURCE/sqlite.ts $DEST/

# Hybrid search (vector + keyword)
cp $SOURCE/hybrid.ts $DEST/

# Helper modules
cp $SOURCE/embedding-inputs.ts $DEST/
cp $SOURCE/embedding-vectors.ts $DEST/
cp $SOURCE/query-expansion.ts $DEST/
cp $SOURCE/temporal-decay.ts $DEST/
```

### Step 3: Session Management

Copy these files to `openclaw-brain/src/sessions/`:

```bash
SOURCE=/tmp/openclaw/src/sessions
DEST="/mnt/c/Drive D/Projects/Antigravity/Follow-up_agent/openclaw-brain/src/sessions"

cp $SOURCE/session-id.ts $DEST/
cp $SOURCE/transcript-events.ts $DEST/
cp $SOURCE/session-key-utils.ts $DEST/
cp $SOURCE/model-overrides.ts $DEST/
cp $SOURCE/send-policy.ts $DEST/
```

### Step 4: Infrastructure & Types

Copy shared utilities:

```bash
SOURCE=/tmp/openclaw/src
DEST="/mnt/c/Drive D/Projects/Antigravity/Follow-up_agent/openclaw-brain/src"

# Core utilities
cp $SOURCE/utils.ts $DEST/

# Logging
mkdir -p $DEST/infra
cp $SOURCE/infra/logger.ts $DEST/infra/

# Types
mkdir -p $DEST/types
cp $SOURCE/types/index.ts $DEST/types/ 2>/dev/null || echo "Types may be in different location"
```

### Step 5: Resolve Dependencies

After copying, you'll need to fix imports. OpenClaw has many internal dependencies we don't need.

**Create a dependency stub file** (`src/stubs.ts`):

```typescript
// Stubs for OpenClaw dependencies we don't need

export const logger = {
  info: console.log,
  error: console.error,
  warn: console.warn,
  debug: console.debug
};

export function getWorkspaceDir() {
  return process.cwd();
}

// Add more stubs as needed when compilation fails
```

**Update imports** in copied files:

```bash
# Find all imports from '../gateway' or '../channels' (we don't need these)
grep -r "from ['\"]\.\.\/gateway" openclaw-brain/src/
grep -r "from ['\"]\.\.\/channels" openclaw-brain/src/

# Replace with stubs or remove
```

### Step 6: Install Dependencies

```bash
cd openclaw-brain
npm install
```

**Expected errors:** You'll likely get TypeScript errors. That's normal. We'll fix them iteratively.

---

## Creating Sarah-Specific Tools

Now create the business logic tools in `openclaw-brain/tools/`:

### Tool 1: decide_next_action.ts

```bash
cat > openclaw-brain/tools/decide_next_action.ts << 'EOF'
// Decision logic for Sarah's follow-up strategy
// Maps to docs/ARCHITECTURE.md Section 4.1

export const decideNextActionTool = {
  name: "decide_next_action",
  description: `Analyze lead state and decide next action based on Sarah's rules.
  
  Rules:
  - Lead replied positively → ESCALATE to owner
  - No response < 30min → WAIT
  - No response 30min-24hr → SMS follow-up #1
  - No response 24hr-72hr → SMS follow-up #2
  - No response > 72hr → CALL via Vapi
  - Lead said "not interested" → STOP
  - Lead booked appointment → ESCALATE
  `,
  parameters: {
    type: "object",
    properties: {
      lead_state: {
        type: "object",
        properties: {
          customer_id: { type: "number" },
          intent: { type: "string" },
          sentiment: { type: "string" },
          last_interaction_at: { type: "string" }
        }
      },
      time_since_last_interaction: { 
        type: "number",
        description: "Seconds since last interaction"
      },
      conversation_summary: { type: "string" }
    },
    required: ["lead_state", "time_since_last_interaction"]
  },
  handler: async (params: any) => {
    const { lead_state, time_since_last_interaction } = params;
    const minutes = time_since_last_interaction / 60;
    
    // Hot lead detection
    if (lead_state.intent === "HOT_LEAD") {
      return {
        action: "ESCALATE",
        reason: "Lead marked as hot - requires owner attention"
      };
    }
    
    // Negative sentiment
    if (lead_state.sentiment === "negative") {
      return {
        action: "STOP",
        reason: "Lead expressed disinterest"
      };
    }
    
    // Time-based follow-up logic
    if (minutes < 30) {
      return {
        action: "WAIT",
        schedule_delay: 30 - minutes,
        reason: "Too soon for follow-up"
      };
    }
    
    if (minutes < 1440) { // 24 hours
      return {
        action: "SMS",
        message: generateFollowup1(lead_state),
        reason: "First follow-up window (30min-24hr)"
      };
    }
    
    if (minutes < 4320) { // 72 hours
      return {
        action: "SMS",
        message: generateFollowup2(lead_state),
        reason: "Second follow-up window (24hr-72hr)"
      };
    }
    
    return {
      action: "CALL",
      reason: "No response after 72 hours - escalate to voice"
    };
  }
};

function generateFollowup1(lead_state: any): string {
  return `Hi ${lead_state.name || 'there'}! Just checking in on your inquiry. Any questions I can help with?`;
}

function generateFollowup2(lead_state: any): string {
  return `Hi ${lead_state.name || 'there'}! I wanted to follow up one more time. Would you like to schedule a quick call?`;
}
EOF
```

### Tool 2: search_similar_conversations.ts

```bash
cat > openclaw-brain/tools/search_similar_conversations.ts << 'EOF'
// Pattern matching tool using OpenClaw's memory system

import { getMemorySearchManager } from '../src/memory/index.js';

export const searchSimilarConversationsTool = {
  name: "search_similar_conversations",
  description: "Find similar past conversations to learn from successful patterns",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string" },
      lead_type: { type: "string" },
      outcome_filter: { 
        type: "string",
        enum: ["won", "lost", "any"],
        default: "any"
      }
    },
    required: ["query"]
  },
  handler: async (params: any) => {
    const memory = await getMemorySearchManager();
    const results = await memory.search(params.query, { limit: 5 });
    
    const filtered = results.filter((r: any) => 
      params.outcome_filter === "any" || 
      r.metadata?.outcome === params.outcome_filter
    );
    
    return {
      similar_conversations: filtered.map((r: any) => ({
        message: r.text,
        outcome: r.metadata?.outcome,
        similarity: r.score,
        lead_type: r.metadata?.lead_type
      }))
    };
  }
};
EOF
```

### Tool 3: Index file

```bash
cat > openclaw-brain/tools/index.ts << 'EOF'
// Export all Sarah tools

export { decideNextActionTool } from './decide_next_action.js';
export { searchSimilarConversationsTool } from './search_similar_conversations.js';

export const sarahTools = [
  decideNextActionTool,
  searchSimilarConversationsTool
];
EOF
```

---

## Creating HTTP API Wrapper

Create `openclaw-brain/src/sarah-brain-api.ts`:

```typescript
import express from 'express';
import { runEmbeddedPiAgent } from './agents/pi-embedded.js';
import { getMemorySearchManager } from './memory/index.js';
import { sarahTools } from '../tools/index.js';

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

app.post('/decide', async (req, res) => {
  try {
    const { lead_context, user_message, channel } = req.body;
    
    const systemPrompt = buildSarahPrompt(lead_context);
    
    const response = await runEmbeddedPiAgent({
      sessionKey: lead_context.phone,
      userMessage: user_message,
      systemPrompt,
      tools: sarahTools,
      model: process.env.DEFAULT_MODEL || 'anthropic/claude-sonnet-4',
      context: lead_context.conversation_history || []
    });
    
    res.json(response);
  } catch (error) {
    console.error('Decision error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/learn', async (req, res) => {
  try {
    const { conversation_id, outcome, messages } = req.body;
    
    const memory = await getMemorySearchManager();
    
    let indexed = 0;
    for (const msg of messages) {
      await memory.index(msg.body, {
        conversation_id,
        outcome,
        lead_type: msg.lead_type,
        sentiment: msg.sentiment
      });
      indexed++;
    }
    
    res.json({ indexed });
  } catch (error) {
    console.error('Learning error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

function buildSarahPrompt(lead_context: any): string {
  return `You are Sarah, an AI Sales Agent for real estate.

Your job: Analyze this lead and decide the next action.

Lead Context:
- Name: ${lead_context.name || "Unknown"}
- Phone: ${lead_context.phone}
- Last interaction: ${lead_context.last_interaction_at}
- Current intent: ${lead_context.intent}
- Sentiment: ${lead_context.sentiment}

Use the decide_next_action tool to determine: WAIT | SMS | CALL | EMAIL | ESCALATE | STOP

If helpful, use search_similar_conversations to find patterns from past successful interactions.
`;
}

app.listen(PORT, () => {
  console.log(`OpenClaw Brain API running on port ${PORT}`);
});
```

---

## Testing the Extraction

### 1. Compile TypeScript

```bash
cd openclaw-brain
npm run build
```

**Fix any TypeScript errors** by:
- Adding missing imports
- Creating stubs for unavailable OpenClaw modules
- Adjusting type definitions

### 2. Test Standalone

```bash
npm run dev
```

Should start on port 3000.

### 3. Test API

```bash
curl http://localhost:3000/health
# Expected: {"status":"ok","uptime":0.123}

curl -X POST http://localhost:3000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "lead_context": {
      "customer_id": 1,
      "phone": "+15551234567",
      "name": "Test Lead",
      "intent": "WAITING_FOR_ANSWER",
      "sentiment": "neutral",
      "last_interaction_at": "2026-03-16T10:00:00Z",
      "conversation_history": []
    },
    "user_message": "Hi, I am interested in your service",
    "channel": "sms"
  }'
```

---

## Troubleshooting

### Error: Cannot find module

**Cause:** Missing OpenClaw dependency

**Fix:** Either copy the missing file OR create a stub

### Error: TypeScript compilation fails

**Cause:** Type mismatches or missing types

**Fix:** 
1. Check if types are in `src/types/`
2. Create type stubs if needed
3. Use `any` temporarily (fix later)

### Error: SQLite error

**Cause:** sqlite-vec not installed properly

**Fix:**
```bash
npm rebuild better-sqlite3
npm rebuild sqlite-vec
```

---

## Success Criteria

- ✅ TypeScript compiles without errors
- ✅ `npm run dev` starts without crashes
- ✅ `/health` endpoint returns 200
- ✅ `/decide` endpoint accepts test request
- ✅ No runtime errors in console

---

## Next Steps

After successful extraction:
1. Integrate with Python layer (create sarah_orchestrator.py)
2. Test full flow: SMS → Orchestrator → Brain → Response
3. Deploy to VPS
4. Monitor logs for issues

---

**Status:** 🔴 Extraction Not Yet Started  
**Estimated Time:** 1-2 days (with troubleshooting)  
**Difficulty:** Medium (TypeScript experience helpful)
