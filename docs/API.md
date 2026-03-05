# API Quick Reference

**Base URL:** `https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod`  
**Auth Header:** `x-api-key: YOUR_API_KEY`

## Core Endpoints

### Customers
- `POST /customers` - Create customer (email/phone/name)
- `GET /customers` - List all customers
- `PATCH /customers/{customer_id}` - Update customer

### Context & Conversations
- `GET /context/{identifier}?by=phone|email|id` - Get customer context
- `POST /log` - Log message (SMS/voice/email)
- `POST /conversation/{context_id}/update` - Update conversation state

### State Management
Update conversation via `/conversation/{context_id}/update`:
- `intent` - WAITING_FOR_ANSWER | FOLLOWUP_1 | FOLLOWUP_2 | NURTURE | ENGAGED
- `sentiment` - positive | neutral | negative
- `summary` - Text summary of conversation

## Example: Log SMS
```json
POST /log
{
  "customer_id": 123,
  "channel": "sms",
  "channel_identifier": "+14165551234",
  "direction": "inbound",
  "message_body": "Yes, I'm interested"
}
```

See `API Usage Guide_v2.md` for detailed specs.
