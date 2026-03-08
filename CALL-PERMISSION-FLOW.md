# Sarah AI - Call Permission Flow (Updated)

## ✅ What Changed

### Before (Calendar-First Approach)
- Sarah would check calendar availability for ALL calls
- Even immediate calls required calendar checking
- Confusing when someone just wanted to talk NOW

### After (Permission-First Approach)
- Sarah asks "Can I call you right now?" for immediate calls
- Calendar checking ONLY for future scheduled appointments
- Clear separation between immediate calls vs future bookings

---

## 🎯 How It Works Now

### Scenario 1: Lead Shows Interest (Warm/Hot)
```
Lead: "Tell me more about the AI chatbot"
Sarah: "Would a quick call be easier? I can explain everything in 5 minutes."
Lead: "Sure"
Sarah: "Great! I'll call you in 1 minute."
→ System triggers VAPI call (no calendar checking needed)
```

### Scenario 2: Lead Wants Future Appointment
```
Lead: "Can we schedule a call for tomorrow at 2pm?"
Sarah: *checks calendar* "Let me check if that time is available..."
Sarah: "Tomorrow at 2pm is open! What's your email to send the confirmation?"
Lead: "john@example.com"
Sarah: *books appointment* "Perfect! You're booked for tomorrow at 2pm."
```

### Scenario 3: Lead Says "Call Me Later"
```
Lead: "Can you call me later today?"
Sarah: "Absolutely! What time works for you?"
Lead: "Around 4pm"
Sarah: *checks calendar* "4pm is available! I'll call you then."
```

---

## 🔑 Key Changes in Code

### 1. Updated System Prompt (app.py lines 98-122)

**New Section: CALL PERMISSION (Primary Goal)**
```
📞 CALL PERMISSION (Primary Goal)
- Your PRIMARY goal is to get permission to call them immediately
- Ask: "Can I call you right now?" or "Want a quick call to discuss this?"
- If YES → Confirm: "Great! I'll call you in 1 minute." (DO NOT use any functions)
- If NO/LATER → Ask when: "No problem! When's a good time for me to call?"
- DO NOT check calendar for immediate calls — just get permission and confirm
```

**Separated Section: APPOINTMENT BOOKING (Only for Future)**
```
📅 APPOINTMENT BOOKING (Only for Future Scheduled Meetings)
Use calendar functions ONLY when they want to schedule a future appointment (not immediate calls):
1. If they mention a specific day/time for a FUTURE meeting → call get_availability
2. If slot is open → ask for their email (you have their phone)
3. Once you have email → call book_appointment to finalize
```

### 2. Updated Function Descriptions (app.py lines 162-199)

**get_availability**
- Before: "Call this ALWAYS when the user suggests a day or time"
- After: "Call this ONLY when the user wants to schedule a FUTURE appointment (not an immediate call)"

**book_appointment**
- Before: "Call this ONLY after the user has confirmed a specific time slot"
- After: "Call this ONLY after checking availability for a FUTURE appointment... This is for scheduled meetings, not immediate calls."

### 3. Updated State Analysis (app.py lines 313-333)

**booking_requested now detects:**
- ✅ Explicit booking requests (future appointments)
- ✅ Agreement to calls ("yes", "sure", "ok", "call me")
- ✅ Callback requests

**interest_level "hot" now includes:**
- ✅ Agrees to call NOW (in addition to pricing/timeline mentions)

---

## 🧪 Testing Scenarios

### Test 1: Immediate Call Request
```
You: "I'm interested in AI chatbots"
Expected: Sarah offers immediate call ("Can I call you right now?")
You: "Yes"
Expected: Sarah confirms ("Great! Calling you now.") WITHOUT checking calendar
✅ PASS if no calendar function is called
```

### Test 2: Future Appointment Request
```
You: "Can we talk tomorrow at 3pm?"
Expected: Sarah checks calendar availability
Expected: Sarah asks for email
Expected: Sarah books appointment
✅ PASS if calendar functions ARE used
```

### Test 3: "Call Me Later" Ambiguous Request
```
You: "Call me later"
Expected: Sarah asks "When's a good time?"
You: "In an hour"
Expected: Sarah confirms without calendar (treats as immediate)
You: "Tomorrow morning"
Expected: Sarah checks calendar (treats as future appointment)
```

---

## 📊 Expected Behavior

| User Input | Sarah's Response | Calendar Check? |
|------------|------------------|-----------------|
| "Can I call you now?" | "Absolutely! Calling you in 1 minute." | ❌ No |
| "Call me back" | "Sure! Can I call you right now or later?" | ❌ No (until time specified) |
| "Call me tomorrow at 2pm" | "Let me check... 2pm is available!" | ✅ Yes |
| "Yes" (after Sarah offered call) | "Great! I'll call you now." | ❌ No |
| "Schedule a consultation" | "What time works for you?" → checks calendar | ✅ Yes (when time given) |

---

## 🚀 Next Steps

1. **Deploy Changes** - Code is already updated
2. **Test Flow** - Send test SMS to verify behavior
3. **Monitor Logs** - Check that calendar functions are NOT called for immediate calls
4. **Update VAPI** - Ensure voice calls match this flow

---

**Last Updated:** March 8, 2026  
**Version:** 2.1 (Call Permission First)
