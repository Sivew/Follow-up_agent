# Architecture Decision — APPROVED WITH CHANGES

**Date:** 2026-03-16  
**Decision By:** Shiva (Product Owner)  
**Status:** 🟡 APPROVED WITH CHANGES

---

## Final Verdict

**APPROVED** — Proceed with OpenClaw Brain integration, with the following modifications.

---

## What's Approved ✅

| Item | Status |
|------|--------|
| Hybrid Architecture (Python shell + TypeScript brain) | ✅ Approved |
| OpenClaw Brain extraction approach | ✅ Approved |
| Hybrid Storage (brain.db + Sarah DB) | ✅ Approved |
| Voice migration to Python (kill Make.com) | ✅ Approved |
| Nightly learning batch | ✅ Approved |

---

## Required Changes 🟡

### 1. Timeline Adjustment — MANDATORY

The proposed 2-3 weeks is too aggressive for extraction + integration + testing + deploy.

**Revised Timeline:**

| Phase | Duration | Target Dates |
|-------|----------|--------------|
| Phase 1: Extract Brain | 1.5 weeks | Mar 16-25 |
| Phase 2: Python Integration | 1.5 weeks | Mar 26 - Apr 2 |
| Phase 3: Deploy & Test | 1 week | Apr 3-9 |
| Phase 4: Production Cutover | 0.5 week | Apr 10-12 |

**Total: 4-5 weeks**

**Important:** Sarah v1 (current SMS flow) can still launch Mar 19. Sarah v2 (OpenClaw Brain) launches Apr 10-12. Do not block v1 for v2.

---

### 2. Verify npm Package Option — BEFORE EXTRACTION

Before manually extracting OpenClaw files, verify:

- [ ] Does OpenClaw expose a standalone npm package we can install?
- [ ] Does OpenClaw have an HTTP API we can call directly?

If either exists → use that instead of extraction (cleaner, easier updates).
If neither exists → proceed with extraction but budget the extra complexity.

**Action:** Spend 2-4 hours on this research before starting Phase 1.

---

### 3. Add Fallback Logic — REQUIRED

The architecture must handle Brain API failures gracefully. Add to `sarah_orchestrator.py`:

```python
def get_decision(self, context):
    """Get decision from Brain API with fallback to v1 logic."""
    try:
        response = self.brain_api.decide(context, timeout=5)
        return response
    except (BrainAPIError, TimeoutError, ConnectionError) as e:
        logger.warning(f"Brain API failed: {e}. Using fallback.")
        return self.fallback_decision(context)

def fallback_decision(self, context):
    """V1-style decision logic when Brain is unavailable."""
    # Use existing followup_strategy.json rules
    # This ensures Sarah never goes silent
    ...
```

**Requirement:** Sarah must NEVER fail silently. If Brain is down, fall back to v1 rules.

---

### 4. Add Health Check & Alerting — REQUIRED

Missing from architecture. Add to Phase 3:

**Health Check Endpoint** (`/health` on Brain API):
```typescript
app.get('/health', (req, res) => {
  const dbOk = checkDatabaseConnection();
  const memoryOk = checkMemorySystem();
  res.json({
    status: dbOk && memoryOk ? 'healthy' : 'degraded',
    db: dbOk,
    memory: memoryOk,
    timestamp: new Date().toISOString()
  });
});
```

**Alerting Requirements:**
- If Brain fails 3x consecutively → Send Telegram alert to owner
- Daily health check summary in logs
- Dashboard (future): Decision quality review

---

### 5. Update Documentation — REQUIRED

Update the following in `ARCHITECTURE_v2_OPENCLAW.md`:

1. Change timeline from "2-3 weeks" to "4-5 weeks"
2. Add fallback logic section under Component Details
3. Add health check/alerting to Phase 3 checklist
4. Note that v1 launches Mar 19, v2 launches Apr 10-12

---

## Questions Answered

| Question | Decision | Rationale |
|----------|----------|-----------|
| Deploy Brain on same VPS or separate? | Same VPS | Lower latency, simpler ops for MVP |
| Hybrid storage approach? | Approved | brain.db for speed, Sarah DB for truth |
| Learning frequency? | Nightly batch | Sufficient for learning, less API load |
| Keep Make.com for voice? | No — migrate to Python | Single codebase, easier debugging |
| Mar 19 launch with v2? | No — v1 launches Mar 19, v2 in April | Don't block working code for new architecture |

---

## Risks Acknowledged

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Extraction takes longer | Medium | Budgeted 1.5 weeks instead of 1 |
| TypeScript maintenance burden | Medium | Document everything, consider npm if available |
| Integration bugs | High | 1 week dedicated testing phase |
| Brain API downtime | Low | Fallback to v1 logic (required) |

---

## Next Steps

1. **Research (2-4 hours):** Check npm package / HTTP API options before extraction
2. **Phase 1 Start:** Mar 16 — Begin extraction per `OPENCLAW_EXTRACTION_GUIDE.md`
3. **Weekly Check-ins:** Every Friday, status update on progress
4. **v1 Launch:** Mar 19 — Current SMS flow goes live for Kalkia
5. **v2 Target:** Apr 10-12 — Full OpenClaw Brain integration live

---

## Approval

```
Decision: APPROVED WITH CHANGES
Date: 2026-03-16
Approved By: Shiva (Product Owner)

Changes Required:
1. Timeline → 4-5 weeks (not 2-3)
2. Verify npm/API option before extraction
3. Add fallback logic (mandatory)
4. Add health check & alerting
5. v1 launches Mar 19, v2 launches Apr 10-12
```

---

**Proceed with Phase 1. Report progress Friday Mar 21.**
