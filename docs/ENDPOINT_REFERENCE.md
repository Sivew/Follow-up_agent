# Endpoint Quick Reference

This document clarifies the **correct endpoints** for the Sarah DB API.

## All 3 Core Endpoints

| Action | Method | Endpoint | Uses |
|--------|--------|----------|------|
| **Get context** | `GET` | `/context/{customer_id}` | `customer_id` (int) or phone with `?by=phone_normalized` |
| **Log message** | `POST` | `/log` | Message body (no ID in URL) |
| **Update context** | `POST` | `/conversation/{context_id}/update` | `context_id` (UUID string) |

---

## Critical Distinction

### ❌ WRONG Endpoint (Common Mistake)
```
POST /context/{context_id}/update
```
This endpoint does NOT exist and will route to the wrong Lambda function.

### ✅ CORRECT Endpoint
```
POST /conversation/{context_id}/update
```
Note: `/conversation/` not `/context/`

---

## Working Examples

### 1. Get Customer Context by Phone
```bash
curl -X GET \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/context/14165551234?by=phone_normalized" \
  -H "x-api-key: YOUR_API_KEY"
```

**Response**:
```json
{
  "customer_id": 132,
  "context_id": "ffc611f6-7dce-41ee-b4e2-e5cbb144d810",
  "phone": "+14165551234",
  "name": "John Doe",
  "summary": "Customer interested in pricing",
  "intent": "WAITING_FOR_ANSWER",
  "sentiment": "positive",
  "history": [...]
}
```

### 2. Log Inbound Message
```bash
curl -X POST \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/log" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 132,
    "channel": "sms",
    "channel_identifier": "+14165551234",
    "direction": "inbound",
    "message_body": "How much does it cost?"
  }'
```

**Response**:
```json
{
  "log_id": 456,
  "context_id": "ffc611f6-7dce-41ee-b4e2-e5cbb144d810"
}
```

### 3. Update Conversation Context
```bash
curl -X POST \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/conversation/ffc611f6-7dce-41ee-b4e2-e5cbb144d810/update" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Customer asked about pricing. Sent pricing details.",
    "intent": "WAITING_FOR_ANSWER",
    "sentiment": "positive"
  }'
```

**Response (Confirmed Working)**:
```json
{
  "success": true,
  "context_id": "ffc611f6-7dce-41ee-b4e2-e5cbb144d810",
  "customer_id": 132,
  "message_count": 19
}
```

---

## Parameter Types

| Parameter | Type | Format | Example |
|-----------|------|--------|---------|
| `customer_id` | Integer | Numeric ID | `132` |
| `context_id` | String (UUID) | UUID v4 | `ffc611f6-7dce-41ee-b4e2-e5cbb144d810` |
| `phone` | String | E.164 format | `+14165551234` |
| `phone_normalized` | String | Digits only | `14165551234` |

---

## Common Mistakes & Fixes

### Mistake 1: Wrong Endpoint Path
```python
# ❌ WRONG
url = f"{base_url}/context/{context_id}/update"

# ✅ CORRECT
url = f"{base_url}/conversation/{context_id}/update"
```

### Mistake 2: Using customer_id Instead of context_id
```python
# ❌ WRONG
db_client.update_conversation(customer_id=132, summary="...")

# ✅ CORRECT
db_client.update_conversation(context_id="ffc611f6-...", summary="...")
```

### Mistake 3: Not URL-Encoding Phone Numbers
```python
# ❌ WRONG (in Make.com or manual URLs)
/context/+14165551234?by=phone_normalized

# ✅ CORRECT
/context/%2B14165551234?by=phone_normalized
# OR (in code)
import urllib.parse
encoded = urllib.parse.quote(phone, safe='')
```

---

## Python Client Usage

### Correct Usage (Updated Code)
```python
from sarah_db_client import SarahDBClient

client = SarahDBClient(api_key="your_key")

# 1. Get context by phone
context = client.get_context("+14165551234", lookup_by="phone")
customer_id = context['customer_id']
context_id = context['context_id']

# 2. Log message
client.log_message(
    customer_id=customer_id,
    channel="sms",
    identifier="+14165551234",
    direction="inbound",
    body="How much does it cost?",
    context_id=context_id
)

# 3. Update conversation (use context_id, NOT customer_id)
client.update_conversation(
    context_id=context_id,  # ← UUID string
    summary="Customer asked about pricing",
    intent="WAITING_FOR_ANSWER",
    sentiment="positive"
)
```

---

## URL Structure Summary

```
Base URL: https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod

GET    /context/{identifier}              → Get customer context
POST   /log                                → Log message
POST   /conversation/{context_id}/update  → Update conversation
POST   /customers                          → Create customer
GET    /customers                          → List customers
```

---

## Notes

1. **Always use `context_id` (UUID) for conversation updates**, not `customer_id`
2. **The endpoint is `/conversation/` not `/context/`** when updating
3. Get the `context_id` from the `/context/{identifier}` GET request response
4. Phone lookups require `?by=phone_normalized` query parameter
5. All requests require `x-api-key` header for authentication
