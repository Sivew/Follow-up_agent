# Make.com Scenario Setup

This guide explains how to set up Make.com scenarios for the Voice AI integration.

## Prerequisites

1. Make.com account
2. Sarah DB API credentials:
   - `CORE_API_URL`: `https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod`
   - `CORE_API_KEY`: Your API key

## Scenario Overview

### Scenario 1: Incoming Call Handler
- **Trigger:** Webhook from Vapi (incoming call)
- **Action:** Fetch customer data from Sarah DB
- **Output:** Return customer info to Vapi

### Scenario 2: Call Ended Handler
- **Trigger:** Webhook from Vapi (call ended)
- **Action 1:** Log call to Sarah DB via `/log`
- **Action 2:** Update conversation context via `/context/{customer_id}/update`
- **Output:** Call recorded in database

## Setup Steps

### Step 1: Configure HTTP Module (Correct Way)

This is the most critical step. Many users get this wrong.

1. **Add HTTP module** to your scenario
2. **DO NOT** use the "Authentication" dropdown for API key
3. Instead, configure it like this:

```
HTTP Module Configuration:
├── Method: GET (or POST)
├── URL: https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/context/{{phone_number}}?by=phone_normalized
├──
├── Headers (click "Show advanced settings" if needed):
│   ├── x-api-key: your_actual_api_key_here
│   └── Content-Type: application/json
│
└── Body type: (for POST only)
    └── raw
```

**IMPORTANT - Common Mistakes:**
- ❌ Don't select "API Key" in Authentication dropdown
- ❌ Don't select "AWS Signature" - that's for AWS services
- ✅ Set Authentication to **"None"**
- ✅ Add headers manually in the Headers section

### Step 2: Set Up Webhooks

#### Incoming Call Webhook
1. Add "Webhook" module as trigger
2. Copy the webhook URL
3. Paste this URL in Vapi dashboard (see `../vapi-setup/configuration.md`)
4. Test the webhook to ensure it's receiving data

#### Call Ended Webhook
1. Add another "Webhook" module
2. Copy the webhook URL
3. Paste in Vapi dashboard for "call ended" event
4. Test the webhook

### Step 3: Configure Customer Lookup

For incoming call scenario:

1. Add "Parse JSON" module to extract phone number from webhook
2. Add "HTTP" module:
   - Method: GET
   - URL: `{{CORE_API_URL}}/context/{{phone_number}}?by=phone_normalized`
   - Headers: Already configured in connection

### Step 4: Configure Call Logging

For call ended scenario:

1. Add "Parse JSON" module to extract:
   - phone_number
   - duration
   - call_status (outcome)
   - timestamp

2. Add "HTTP" module for `/log`:
   - Method: POST
   - URL: `{{CORE_API_URL}}/log`
   - Body:
   ```json
   {
     "customer_id": {{customer_id}},
     "channel": "voice",
     "channel_identifier": "{{phone_number}}",
     "direction": "outbound",
     "message_body": "{{call_summary}}",
     "metadata": {
       "duration": {{duration}},
       "outcome": "{{call_status}}",
       "phone": "{{phone_number}}",
       "timestamp": "{{timestamp}}"
     }
   }
   ```

3. Add "HTTP" module for `/context/{customer_id}/update`:
   - Method: POST
   - URL: `{{CORE_API_URL}}/context/{{customer_id}}/update`
   - Body:
   ```json
   {
     "summary": "{{conversation_summary}}",
     "intent": "{{intent_based_on_outcome}}",
     "last_agent_action": "Voice call completed"
   }
   ```

## Importing Scenarios

### Option 1: Manual Setup
Follow the steps above to create scenarios manually.

### Option 2: Import JSON
If you have the scenario JSON files:
1. In Make.com, click "Import Blueprint"
2. Upload the JSON file
3. Update connections with your credentials

## Scenario Execution Flow

### Incoming Call Flow
```
Vapi Webhook → Parse JSON → HTTP GET /context → Return to Vapi
```

### Call Ended Flow
```
Vapi Webhook → Parse JSON → HTTP POST /log → HTTP POST /context/update → Done
```

## Testing

### Test Incoming Call
1. Configure webhook in Vapi
2. Make a test call
3. Check Make.com execution history
4. Verify API response contains customer data

### Test Call Ended
1. Let a call end naturally
2. Check Make.com execution history
3. Verify:
   - Call logged in `/log` endpoint
   - Context updated in `/context/{customer_id}/update`

## Common Issues

### 403 Forbidden - AWS Signature Error
**Error:** `Authorization header requires 'Credential' parameter`
**Cause:** Make.com is trying to use AWS authentication
**Fix:** 
- Set Authentication dropdown to **"None"**
- Add headers manually (see Step 1 above)

### 403 Forbidden - Missing Token
**Error:** `Missing Authentication Token`
**Cause:** API key not being passed correctly
**Fix:**
- Verify Authentication is set to **"None"**
- Check header name is exactly `x-api-key` (lowercase, with hyphen)
- Make sure header value is your actual API key (not empty, not wrapped in {{}})

### Customer Not Found
- Ensure phone number format matches (use normalized)
- Customer may need to be created first

### Webhook Not Triggering
- Verify webhook URLs are correct in Vapi
- Check Vapi is configured to send webhooks
- Test webhook with Vapi's test feature

## Environment Variables

Store these in Make.com as variables or connections:
```
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
CORE_API_KEY=your_actual_api_key_here
```

## Next Steps

After setup:
1. Test with a real call
2. Verify data appears in Sarah DB
3. Customize summary generation as needed
