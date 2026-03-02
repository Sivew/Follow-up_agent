# Voice AI Integration - Overview

This module enables voice call handling via Vapi + Make.com with the Sarah DB API.

## Architecture

```
Incoming Voice Call (Vapi)
        ↓
   Make.com Webhook
        ↓
   1. Lookup Customer → GET /context/{phone}?by=phone_normalized
        ↓
   Return Customer Data to Vapi
        ↓
   Voice Conversation
        ↓
   Call Ends (Vapi webhook)
        ↓
   2. Log Call → POST /log (channel=voice)
        ↓
   3. Update Context → POST /context/{customer_id}/update
```

## Folder Structure

```
voice-ai/
├── README.md                    # This file
├── make-scenario/               # Make.com scenarios
│   ├── incoming-call.json       # Handle incoming call
│   ├── call-ended.json          # Handle call ended
│   └── setup.md                 # Setup instructions
├── vapi-setup/                  # Vapi configuration
│   └── configuration.md         # Webhook setup
└── api/                         # API call templates
    ├── customer-lookup.json      # GET /context
    ├── log-call.json            # POST /log
    └── update-context.json       # POST /context/{id}/update
```

## Prerequisites

1. **Vapi Account** - Set up voice assistant
2. **Make.com Account** - Create scenarios
3. **Sarah DB API** - Core API access (CORE_API_KEY)

## Setup Steps

### 1. Vapi Setup
See `vapi-setup/configuration.md` to configure:
- Incoming call webhook
- Call ended webhook

### 2. Make.com Setup
See `make-scenario/setup.md` to:
- Import scenarios
- Configure API connections
- Set up webhooks

### 3. API Templates
Use templates in `api/` folder for:
- Customer lookup
- Call logging
- Context updates

## Data Flow

### Incoming Call
1. Vapi receives call from `+1XXXXXXXXXX`
2. Vapi calls Make webhook with phone number
3. Make calls `GET /context/{phone}?by=phone_normalized`
4. Returns customer data to Vapi
5. Vapi uses customer context for personalized conversation

### Call Ended
1. Vapi detects call ended
2. Calls Make webhook with call metadata
3. Make logs call via `POST /log`:
   - channel: "voice"
   - metadata: { duration, outcome, phone, timestamp }
   - message_body: Brief 1-2 sentence summary
4. Make updates context via `POST /context/{customer_id}/update`:
   - summary: Conversation summary
   - intent: Based on outcome

## Supported Metadata Fields

### Call Log Metadata
| Field | Type | Description |
|-------|------|-------------|
| duration | integer | Call duration in seconds |
| outcome | string | "completed", "voicemail", "no_answer", "failed" |
| phone | string | Phone number called |
| timestamp | string | ISO 8601 timestamp |

### Message Body (Short Summary)
- 1-2 sentences summarizing the call
- Example: "Customer interested in enterprise pricing. Scheduled follow-up call for next week."

## Environment Variables

Ensure these are set in Make.com:
```
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
CORE_API_KEY=your_api_key
```

## Testing

1. Use ngrok or similar to test webhooks locally
2. Test incoming call flow with test phone number
3. Verify data appears in Sarah DB
