# Vapi Configuration

This guide explains how to configure Vapi webhooks for the Voice AI integration.

## Prerequisites

- Vapi account with voice assistant set up
- Make.com webhook URLs (after setting up scenarios)

## Webhook Types

### 1. Incoming Call Webhook

This webhook fires when a call comes in. Use it to fetch customer data before the conversation starts.

**Vapi Dashboard Settings:**
1. Go to your Vapi dashboard
2. Navigate to your voice assistant
3. Find "Server Messages" or "Webhooks"
4. Add your Make.com webhook URL

**Webhook URL Format:**
```
https://hook.make.com/your-unique-webhook-id
```

**Payload Received from Vapi:**
```json
{
  "message": {
    "type": "transcript",
    "role": "user",
    "message": {
      "type": "voice-start",
      "call": {
        "id": "call_xxxxxxxx",
        "phone_number": "+14165551234",
        "status": "in-progress"
      }
    }
  }
}
```

**Key Fields:**
- `call.phone_number` - The customer's phone number
- `call.id` - Unique call identifier

### 2. Call Ended Webhook

This webhook fires when the call ends. Use it to log the call and update context.

**Webhook URL Format:**
```
https://hook.make.com/your-unique-webhook-id-call-ended
```

**Payload Received from Vapi:**
```json
{
  "message": {
    "type": "hang",
    "message": {
      "type": "voice-end",
      "call": {
        "id": "call_xxxxxxxx",
        "phone_number": "+14165551234",
        "status": "ended",
        "duration": 180
      }
    }
  }
}
```

**Key Fields:**
- `call.phone_number` - The customer's phone number
- `call.id` - Unique call identifier
- `call.duration` - Call duration in seconds
- `call.status` - "ended", "no-answer", "voicemail", "failed"

## Vapi Dashboard Setup Steps

### Step 1: Get Your Make.com Webhook URLs

After setting up Make.com scenarios (see `../make-scenario/setup.md`), you'll have:
- Incoming call webhook URL
- Call ended webhook URL

### Step 2: Configure Vapi

1. **Login to Vapi Dashboard**
2. **Select your assistant** or create new one
3. **Go to Settings** → **Server Messages** or **Webhooks**
4. **Add Webhook for Incoming Call:**
   - URL: Your Make.com incoming call webhook
   - Events: Select "Call Start" or "Incoming Call"

5. **Add Webhook for Call Ended:**
   - URL: Your Make.com call ended webhook
   - Events: Select "Call End" or "Hang"

### Step 3: Test Configuration

1. Make a test call to your Vapi number
2. Check Make.com execution history
3. Verify data flows correctly

## Environment Variables in Vapi

Vapi doesn't require special env vars for this integration. The logic is handled in Make.com.

## Supported Call Outcomes

| Status | Meaning |
|--------|---------|
| `ended` | Call completed normally |
| `no-answer` | Call was not answered |
| `voicemail` | Call went to voicemail |
| `failed` | Call failed to connect |

## Troubleshooting

### Webhook Not Firing
- Verify webhook URLs are correct in Vapi dashboard
- Check Make.com webhook is active
- Test with Vapi's built-in webhook tester

### Data Not Logging
- Check Make.com execution logs
- Verify API credentials are correct
- Ensure customer exists in Sarah DB

### Phone Number Format
- Vapi sends phone numbers in E.164 format (e.g., `+14165551234`)
- Use `phone_normalized` for API lookups
