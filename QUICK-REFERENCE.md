# Sarah AI - Quick Reference Card

## 🎯 New Qualification Strategy (DISCOVER → QUALIFY → ESCALATE)

### DISCOVER Questions (Sarah asks these automatically)
- What's their business/role?
- What problem are they solving?

### QUALIFY Criteria (AI automatically scores)
- Timeline: Exploring vs actively looking?
- Authority: Decision-maker or info gatherer?
- Urgency: "Soon" vs "just researching"

### ESCALATE Rules (Automatic)
| Interest Level | Action |
|----------------|--------|
| **HOT** (timeline/pricing/ready) | Offer immediate call |
| **WARM** (asks questions/engaged) | Suggest consultation booking |
| **COLD** (short replies/browsing) | Value-driven follow-ups |

---

## 📦 Products & Services (All 4)

1. **AI Receptionist** - Bilingual, books appointments, takes orders
2. **AI Sales Agents** - Makes calls, closes deals, captures leads  
3. **AI Chatbots** - Website/ecosystem integration
4. **Custom Automation Agents** - Tailored business workflows

---

## ⏰ Follow-up Cadence (New)

| Timing | Message Type | Goal |
|--------|--------------|------|
| **30 minutes** | Value-driven reference to their interest | Re-engage |
| **24 hours** | Offer phone call as alternative | Escalate to voice |
| **48 hours** | Soft close with open door | Nurture long-term |

---

## 🔥 Hot Lead Triggers

Sarah marks as **HOT_LEAD** when:
- ✅ Explicit booking request
- ✅ Interest level = "hot" + call recommended
- ✅ Mentions timeline or pricing
- ✅ Says "ready to talk"

---

## 📊 New CRM Fields (8 total)

### Original (5)
1. `summary` - Conversation summary
2. `sentiment` - positive/neutral/negative/confused
3. `extracted_name` - Lead's name
4. `extracted_email` - Lead's email  
5. `booking_requested` - Explicit booking request

### New (3)
6. **`interest_level`** - cold/warm/hot
7. **`product_interest`** - Which of 4 products
8. **`call_recommended`** - Should trigger voice call?

---

## 🎙️ Voice Call Integration

### Current State
- Voice calls triggered manually or on booking request
- VAPI prompt aligned with SMS qualification framework
- Sarah references SMS conversation history on calls

### To Fully Automate (TODO)
1. Add `VAPI_WEBHOOK_URL` to `.env`
2. Create `trigger_vapi_call()` function
3. Uncomment voice trigger logic in `app.py` (lines 507-520)

---

## 🧪 Testing Commands

### Test SMS Flow
```bash
# Send test SMS to your Twilio number
# Check logs: docker logs -f follow-up-agent
```

### View State Analysis Output
```bash
# Look for this in logs:
# DEBUG: Interest Level: warm, Product Interest: ai_chatbot, Call Recommended: true
```

### Test Follow-up Timing
```bash
# Monitor cron worker
docker logs -f follow-up-agent | grep "FOLLOWUP"
```

---

## 📝 Quick Edits

### Change Follow-up Timing
Edit `followup_strategy.json`:
- `wait_minutes: 30` → First follow-up delay
- `wait_minutes: 1440` → Second follow-up (24 hrs)
- `wait_minutes: 2880` → Third follow-up (48 hrs)

### Adjust Interest Detection
Edit `app.py` lines 300-318:
- Modify criteria for "hot" vs "warm" vs "cold"
- Add/remove signals for `call_recommended`

### Change Product Catalog
Edit `app.py` lines 106-112:
- Add/remove products from the list
- Update descriptions

---

## 🚨 Common Issues & Fixes

### Issue: Sarah not asking discovery questions
**Fix:** Check that conversation history is being passed correctly

### Issue: Interest level always "cold"
**Fix:** Verify state analysis prompt is receiving user input properly

### Issue: Follow-ups not sending
**Fix:** Check cron_worker logs for errors, verify intent state transitions

### Issue: VAPI call doesn't reference SMS history
**Fix:** Ensure `Incoming_call_check_user` tool is being called first

---

## 📞 Manual VAPI Prompt Update

1. Open: `voice-ai/VAPI-PROMPT-REVISED.md`
2. Copy prompt (from "## Identity & Purpose" onwards)
3. VAPI Dashboard → Assistant → System Prompt
4. Paste and Save

---

**Last Updated:** March 5, 2026  
**Version:** 2.0
