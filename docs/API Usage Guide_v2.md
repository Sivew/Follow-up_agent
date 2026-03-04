# API Usage Guide v2 - Complete Reference

**Version:** 2.1 (Verified & Tested)  
**Last Updated:** March 2, 2026  
**Base URL:** `https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod`

---

## IMPORTANT NOTICE

**Do NOT query the database directly.** Use these API endpoints for all data operations. If you need data in a different format or additional fields, contact the team lead.

---

## Authentication

All API requests require an API key in the header:

```
Header: x-api-key: YOUR_API_KEY
Content-Type: application/json
```

---

## Currently Deployed & Verified Endpoints

These endpoints have been tested and confirmed working:

| Method | Endpoint | Lambda | Status |
|--------|----------|--------|--------|
| `GET` | `/context/{customer_id}` | get_context | VERIFIED |
| `POST` | `/log` | log_message | VERIFIED |
| `POST` | `/conversation/{context_id}/update` | update_context | VERIFIED |

### Not Yet Deployed

The following endpoints from the original guide require additional Lambda deployment:

- `/customers/*` endpoints (customers Lambda)
- `/messages/*` endpoints (messages Lambda)  
- `/conversations/*` endpoints (conversations Lambda)

Contact team lead if you need these endpoints activated.

---

## URL Encoding (CRITICAL)

When using special characters in URL path parameters (email, phone), you **MUST** URL-encode them:

| Character | Encoded | Example |
|-----------|---------|---------|
| `@` | `%40` | `john%40example.com` |
| `+` | `%2B` | `%2B14165551234` |
| Space | `%20` | `John%20Doe` |

**Failure to URL-encode will result in "Forbidden" errors.**

---

## Verified Endpoints Detail

---

### 1. Get Conversation Context

**Purpose:** Look up customer information and conversation state. This is your **PRIMARY entry point** when a new message arrives.

**Endpoint:** `GET /context/{identifier}?by={lookup_type}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `identifier` | string | Customer ID, email, or phone (URL-encoded) |

**Query Parameters:**

| Parameter | Required | Values | Default |
|-----------|----------|--------|---------|
| `by` | No | `id`, `email`, `phone_normalized` | `id` |

**IMPORTANT:** For phone lookups, use `phone_normalized` (E.164 format like `+14165551234`)

---

#### Example Requests (All Verified Working)

**By Customer ID:**
```bash
curl -X GET \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/context/2" \
  -H "x-api-key: YOUR_API_KEY"
```

**By Email:**
```bash
curl -X GET \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/context/sarah.m%40gmail.com?by=email" \
  -H "x-api-key: YOUR_API_KEY"
```

**By Phone (E.164 format):**
```bash
curl -X GET \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/context/%2B14385559876?by=phone_normalized" \
  -H "x-api-key: YOUR_API_KEY"
```

---

#### Response - Existing Conversation (is_new: false)

When the customer has an **active** or **paused** conversation:

```json
{
  "context_id": "e36cf42d-fd33-4129-9541-fbc89146e899",
  "customer_id": 2,
  "customer": {
    "customer_id": 2,
    "name": "Sarah Miller",
    "email": "sarah.m@gmail.com",
    "phone": "(438) 555-9876"
  },
  "status": "active",
  "summary": "Customer inquiring about enterprise pricing",
  "intent": "pricing_inquiry",
  "sentiment": "positive",
  "last_channel": "email",
  "last_interaction_at": "2026-03-02T23:09:55.540787",
  "message_count": 1,
  "open_questions": null,
  "last_agent_action": "Acknowledged inquiry, preparing pricing info",
  "history": [
    {
      "direction": "inbound",
      "message_body": "Hi, I am interested in your enterprise plan...",
      "message_subject": "Pricing Inquiry",
      "channel": "email",
      "created_at": "2026-03-02T23:09:46.135994"
    }
  ],
  "is_new": false
}
```

---

#### Response - New Conversation (is_new: true)

When the customer has NO active/paused conversation:

```json
{
  "context_id": null,
  "customer_id": 2,
  "customer": {
    "customer_id": 2,
    "name": "Sarah Miller",
    "email": "sarah.m@gmail.com",
    "phone": "(438) 555-9876",
    "company": null
  },
  "summary": "New conversation - no active/paused context",
  "history": [],
  "previous_conversations": [],
  "is_new": true
}
```

---

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `context_id` | UUID/null | Conversation ID. `null` if new conversation needed. |
| `customer_id` | integer | Customer ID in CRM |
| `customer` | object | Customer details |
| `is_new` | boolean | `true` = start new conversation, `false` = continue existing |
| `status` | string | `active` or `paused` (only when is_new=false) |
| `summary` | string | Conversation summary |
| `intent` | string | Current detected intent |
| `sentiment` | string | Customer sentiment |
| `last_channel` | string | Last communication channel |
| `last_interaction_at` | ISO datetime | Timestamp of last interaction |
| `message_count` | integer | Messages in conversation |
| `open_questions` | string/null | Pending follow-up questions |
| `last_agent_action` | string/null | What AI/agent last did |
| `history` | array | Last 10 messages (most recent first) |
| `previous_conversations` | array | Past conversations (only when is_new=true) |

---

### 2. Log Message

**Purpose:** Record any message (inbound from customer OR outbound to customer). Automatically creates a new conversation if needed.

**Endpoint:** `POST /log`

**Headers:**
```
Content-Type: application/json
x-api-key: YOUR_API_KEY
```

---

#### Request Body

```json
{
  "customer_id": 2,
  "channel": "email",
  "channel_identifier": "sarah.m@gmail.com",
  "direction": "inbound",
  "message_body": "Hi, I am interested in your enterprise plan.",
  "message_subject": "Pricing Inquiry",
  "context_id": "e36cf42d-fd33-4129-9541-fbc89146e899",
  "metadata": {"source": "gmail"},
  "send_status": "sent"
}
```

**Required Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | integer | Customer ID from CRM |
| `channel` | string | `email`, `chat`, `voice`, `sms`, `whatsapp`, `social` |
| `channel_identifier` | string | Email, phone, or social handle |
| `direction` | string | `inbound` (from customer) or `outbound` (to customer) |
| `message_body` | string | The message content |

**Optional Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `message_subject` | string | null | Email subject line |
| `context_id` | UUID | auto | If omitted, uses active or creates new |
| `metadata` | object | {} | Extra data (Twilio SID, thread ID, etc.) |
| `send_status` | string | `sent` | `sent`, `pending`, `failed` |

---

#### Example Request (Verified Working)

```bash
curl -X POST \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/log" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 2,
    "channel": "email",
    "channel_identifier": "sarah.m@gmail.com",
    "direction": "inbound",
    "message_body": "Hi, I am interested in your enterprise plan. Can you send me pricing details?",
    "message_subject": "Pricing Inquiry"
  }'
```

---

#### Response

```json
{
  "success": true,
  "log_id": 79,
  "context_id": "e36cf42d-fd33-4129-9541-fbc89146e899"
}
```

**Important:** 
- Save the returned `context_id` for subsequent calls
- If no `context_id` was provided, the API either used an existing active conversation or created a new one

---

### 3. Update Context

**Purpose:** Update conversation state after AI/agent processes a message.

**Endpoint:** `POST /conversation/{context_id}/update`

**Note:** The path is `/conversation/` (singular) NOT `/context/`

**Headers:**
```
Content-Type: application/json
x-api-key: YOUR_API_KEY
```

---

#### Request Body

All fields are **optional**. Include only what you want to update.

```json
{
  "summary": "Customer inquiring about enterprise pricing",
  "intent": "pricing_inquiry",
  "sentiment": "positive",
  "last_message_preview": "Customer asked about pricing",
  "last_channel": "email",
  "open_questions": "Need to confirm team size",
  "last_agent_action": "Sent pricing information"
}
```

**Allowed Fields:**

| Field | Type | Maps To (DB) | Description |
|-------|------|--------------|-------------|
| `summary` | string | conversation_summary | Conversation summary |
| `intent` | string | active_intent | Detected intent |
| `sentiment` | string | current_sentiment | `positive`, `neutral`, `negative`, `frustrated` |
| `last_message_preview` | string | last_message_preview | Short preview (max 200 chars) |
| `last_channel` | string | last_channel | Last channel used |
| `open_questions` | string | open_questions | Pending follow-up questions |
| `last_agent_action` | string | last_agent_action | What AI/agent did |

**Auto-Updated Fields:**

These are automatically updated on every call:
- `last_interaction_at` = current timestamp
- `message_count` = incremented by 1
- `updated_at` = current timestamp
- All unprocessed messages marked as `processed = TRUE`

---

#### Example Request (Verified Working)

```bash
curl -X POST \
  "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/conversation/e36cf42d-fd33-4129-9541-fbc89146e899/update" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Customer inquiring about enterprise pricing",
    "intent": "pricing_inquiry",
    "sentiment": "positive",
    "last_agent_action": "Acknowledged inquiry, preparing pricing info"
  }'
```

---

#### Response

```json
{
  "success": true,
  "context_id": "e36cf42d-fd33-4129-9541-fbc89146e899",
  "customer_id": 2,
  "message_count": 1
}
```

---

## Complete Workflow

Here's the recommended flow when processing an incoming message:

```
1. MESSAGE ARRIVES (email, SMS, chat, etc.)
        |
        v
2. GET CONTEXT
   GET /context/{email}?by=email
   
   Check response:
   - is_new: true  --> No active conversation (context_id is null)
   - is_new: false --> Active conversation exists (use context_id)
        |
        v
3. LOG INBOUND MESSAGE
   POST /log
   {
     "customer_id": <from step 2>,
     "channel": "email",
     "channel_identifier": <email/phone>,
     "direction": "inbound",
     "message_body": <the message>,
     "context_id": <from step 2, or omit if null>
   }
   
   --> Returns: log_id, context_id (save this!)
        |
        v
4. AI/BRAIN PROCESSES MESSAGE
   - Use history[] from step 2 for context
   - Use summary/intent/sentiment for understanding
   - Generate response
        |
        v
5. LOG OUTBOUND MESSAGE
   POST /log
   {
     "customer_id": <same>,
     "channel": "email",
     "channel_identifier": <email/phone>,
     "direction": "outbound",
     "message_body": <AI response>,
     "context_id": <from step 3>
   }
        |
        v
6. UPDATE CONTEXT
   POST /conversation/{context_id}/update
   {
     "summary": <AI-generated summary>,
     "intent": <detected intent>,
     "sentiment": <detected sentiment>,
     "last_agent_action": <what AI did>
   }
```

---

## Conversation Status Values

| Status | Meaning | Description |
|--------|---------|-------------|
| `active` | Ongoing | Default for new conversations |
| `paused` | Cold lead | Follow up later |
| `resolved` | Converted | Lead became customer |
| `archived` | Dead lead | No further action |

**Note:** Status changes are not yet exposed via API. Contact team lead if needed.

---

## Channel Values

| Channel | Value |
|---------|-------|
| Email | `email` |
| SMS | `sms` |
| Chat/Chatbot | `chat` |
| Voice/Phone | `voice` |
| WhatsApp | `whatsapp` |
| Social Media | `social` |

---

## Error Responses

All errors return:

```json
{
  "error": "Error message description"
}
```

**HTTP Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Missing/invalid parameters |
| 403 | Forbidden - Invalid/missing API key |
| 404 | Not Found - Customer/context not found |
| 500 | Server Error - Contact team lead |

**Common Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing customer_id parameter` | No identifier in path | Include ID/email/phone in URL |
| `Customer not found with email: xxx` | Email not in CRM | Verify spelling or add customer first |
| `Invalid lookup method: xxx` | Invalid `by` param | Use `id`, `email`, or `phone_normalized` |
| `Missing required fields: [...]` | Incomplete body | Include all required fields |
| `Context {id} not found` | Invalid context_id | Get fresh context_id from /context |
| `No update fields provided` | Empty body | Include at least one field |
| `Forbidden` | Unencoded special chars | URL-encode `@` as `%40`, `+` as `%2B` |

---

## Code Examples

### Python

```python
import requests
from urllib.parse import quote

BASE_URL = "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod"
API_KEY = "YOUR_API_KEY"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def process_incoming_message(email: str, message_body: str, subject: str = None):
    """Complete workflow for processing an incoming message."""
    
    # Step 1: Get context by email
    encoded_email = quote(email, safe='')
    response = requests.get(
        f"{BASE_URL}/context/{encoded_email}?by=email",
        headers=headers
    )
    context = response.json()
    
    if "error" in context:
        raise Exception(f"Context lookup failed: {context['error']}")
    
    customer_id = context["customer_id"]
    context_id = context.get("context_id")  # May be None
    is_new = context["is_new"]
    
    print(f"Customer: {context['customer']['name']}, New: {is_new}")
    
    # Step 2: Log inbound message
    log_payload = {
        "customer_id": customer_id,
        "channel": "email",
        "channel_identifier": email,
        "direction": "inbound",
        "message_body": message_body
    }
    if subject:
        log_payload["message_subject"] = subject
    if context_id:
        log_payload["context_id"] = context_id
    
    log_response = requests.post(f"{BASE_URL}/log", headers=headers, json=log_payload)
    log_result = log_response.json()
    context_id = log_result["context_id"]
    
    print(f"Logged: log_id={log_result['log_id']}, context_id={context_id}")
    
    # Step 3: AI processing (your logic here)
    ai_response = "Thank you for your interest! I'd be happy to help..."
    
    # Step 4: Log outbound message
    requests.post(f"{BASE_URL}/log", headers=headers, json={
        "customer_id": customer_id,
        "channel": "email",
        "channel_identifier": email,
        "direction": "outbound",
        "message_body": ai_response,
        "context_id": context_id
    })
    
    # Step 5: Update context
    requests.post(f"{BASE_URL}/conversation/{context_id}/update", headers=headers, json={
        "summary": "Customer inquiry about enterprise plan",
        "intent": "pricing_inquiry",
        "sentiment": "positive",
        "last_agent_action": "Sent initial response"
    })
    
    return {"context_id": context_id, "response": ai_response}

# Usage
result = process_incoming_message(
    email="sarah.m@gmail.com",
    message_body="Hi, I'm interested in your enterprise plan.",
    subject="Pricing Inquiry"
)
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod';
const API_KEY = 'YOUR_API_KEY';

const headers = {
  'x-api-key': API_KEY,
  'Content-Type': 'application/json'
};

async function processIncomingMessage(email, messageBody, subject = null) {
  // Step 1: Get context
  const encodedEmail = encodeURIComponent(email);
  const contextRes = await axios.get(
    `${BASE_URL}/context/${encodedEmail}?by=email`,
    { headers }
  );
  const context = contextRes.data;
  
  const customerId = context.customer_id;
  let contextId = context.context_id;
  
  console.log(`Customer: ${context.customer.name}, New: ${context.is_new}`);
  
  // Step 2: Log inbound message
  const logPayload = {
    customer_id: customerId,
    channel: 'email',
    channel_identifier: email,
    direction: 'inbound',
    message_body: messageBody
  };
  if (subject) logPayload.message_subject = subject;
  if (contextId) logPayload.context_id = contextId;
  
  const logRes = await axios.post(`${BASE_URL}/log`, logPayload, { headers });
  contextId = logRes.data.context_id;
  
  // Step 3: AI processing (your logic)
  const aiResponse = "Thank you for your interest!";
  
  // Step 4: Log outbound
  await axios.post(`${BASE_URL}/log`, {
    customer_id: customerId,
    channel: 'email',
    channel_identifier: email,
    direction: 'outbound',
    message_body: aiResponse,
    context_id: contextId
  }, { headers });
  
  // Step 5: Update context
  await axios.post(`${BASE_URL}/conversation/${contextId}/update`, {
    summary: 'Customer inquiry about enterprise plan',
    intent: 'pricing_inquiry',
    sentiment: 'positive',
    last_agent_action: 'Sent initial response'
  }, { headers });
  
  return { contextId, response: aiResponse };
}
```

---

## Rate Limits

| Limit | Value |
|-------|-------|
| Requests/second | 100 |
| Burst limit | 200 |
| Monthly quota | 1,000,000 |

---

## Support & Change Requests

- **Questions:** Contact team lead
- **New fields/endpoints:** Submit request to team lead
- **Database access:** NOT PERMITTED
- **Creating endpoints:** Requires approval

---

## Quick Reference Card

```bash
# Get context by customer ID
GET /context/123

# Get context by email (URL-encode @)
GET /context/user%40example.com?by=email

# Get context by phone (URL-encode +)
GET /context/%2B14165551234?by=phone_normalized

# Log a message
POST /log
{"customer_id":123, "channel":"email", "channel_identifier":"user@example.com", 
 "direction":"inbound", "message_body":"Hello"}

# Update context (note: /conversation/ not /context/)
POST /conversation/{context_id}/update
{"summary":"...", "intent":"...", "sentiment":"..."}
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | Mar 2, 2026 | Verified all 3 endpoints with live testing. Clarified phone uses `phone_normalized`. Fixed update path to `/conversation/`. |
| 2.0 | Feb 2026 | Added planned CRUD endpoints |
| 1.0 | Feb 2026 | Initial release |
