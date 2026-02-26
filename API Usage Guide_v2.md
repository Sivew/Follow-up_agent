# API Usage Guide v2 - Complete Reference

**Version:** 2.0  
**Last Updated:** February 2026  
**Base URL:** `https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod`

---

## Authentication

All API requests require an API key in the header:

```
Header: x-api-key: YOUR_API_KEY
Content-Type: application/json
```

---

## Quick Reference

### All Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| | | **CUSTOMERS** |
| `POST` | `/customers` | Create a new customer |
| `GET` | `/customers` | List/search all customers |
| `GET` | `/customers/{id}` | Get customer by ID, email, or phone |
| `PUT` | `/customers/{id}` | Update customer details |
| `DELETE` | `/customers/{id}` | Delete a customer |
| `POST` | `/customers/lookup` | Find customer by email or phone |
| `POST` | `/customers/upsert` | Create or update customer by email |
| | | **CONTEXT** |
| `GET` | `/context/{identifier}` | Get conversation context by ID/email/phone |
| `POST` | `/context/{customer_id}/update` | Update conversation details |
| | | **MESSAGES** |
| `POST` | `/log` | Log a new message (creates conversation if needed) |
| `GET` | `/messages` | List/search messages |
| `GET` | `/messages/{log_id}` | Get single message by ID |
| `GET` | `/messages/context/{context_id}` | Get all messages in a conversation |
| `GET` | `/messages/customer/{customer_id}` | Get all messages for a customer |
| `PUT` | `/messages/{log_id}/status` | Update message delivery status |
| `POST` | `/messages/{log_id}/processed` | Mark message as processed |
| `POST` | `/messages/context/{context_id}/processed` | Mark all messages in conversation as processed |
| `GET` | `/messages/unprocessed` | Get all unprocessed messages |
| `GET` | `/messages/failed` | Get all failed messages |
| | | **CONVERSATIONS** |
| `GET` | `/conversations` | List/search conversations |
| `GET` | `/conversations/{context_id}` | Get conversation by ID |
| `GET` | `/conversations/customer/{customer_id}` | Get active conversation for customer |
| `POST` | `/conversations` | Create new conversation |
| `PUT` | `/conversations/{context_id}` | Update conversation |
| `POST` | `/conversations/{context_id}/close` | Close/resolve/archive conversation |
| `POST` | `/conversations/get-or-create` | Get existing or create new conversation |

---

## URL Encoding

When using special characters in identifiers (email, phone), URL-encode them:

| Character | Encoded |
|-----------|---------|
| `@` | `%40` |
| `+` | `%2B` |
| Space | `%20` |
| `.` | `%2E` |

---

## Endpoints Detail

---

### CUSTOMERS

---

#### 1. Create Customer

**When to use:** A new person contacts you (e.g., new phone number, new email) and you need to create a record in the CRM.

**Endpoint:** `POST /customers`

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1 416 555 1234",
  "phone_normalized": "+14165551234",
  "company": "Acme Corp"
}
```

**Required:** At least one of `email` or `phone`

**Response (201):**
```json
{
  "customer_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1 416 555 1234",
  "phone_normalized": "+14165551234",
  "company": "Acme Corp",
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-20T10:30:00"
}
```

**Curl:**
```bash
curl -X POST "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/customers" \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","phone":"+14165551234","phone_normalized":"+14165551234"}'
```

---

#### 2. List/Search Customers

**When to use:** You need to find customers by name, email, phone, or company.

**Endpoint:** `GET /customers`

**Query Parameters:**
| Param | Description |
|-------|-------------|
| `email` | Filter by email |
| `phone` | Filter by phone |
| `company` | Filter by company |
| `name` | Filter by name (partial match) |
| `limit` | Number of results (default: 100) |
| `offset` | Pagination offset |

**Response (200):**
```json
{
  "customers": [
    {"customer_id": 123, "name": "John Doe", "email": "john@example.com", ...}
  ],
  "count": 1
}
```

**Curl:**
```bash
curl -X GET "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/customers?company=Acme" \
  -H "x-api-key: YOUR_KEY"
```

---

#### 3. Get Customer by ID/Email/Phone

**When to use:** You know the customer's identifier and want their full details.

**Endpoint:** `GET /customers/{identifier}?by=id|email|phone|external_id`

**Examples:**
```bash
# By customer ID
GET /customers/123

# By email
GET /customers/john%40example.com?by=email

# By phone
GET /customers/%2B14165551234?by=phone

# By external CRM ID
GET /customers/CRM-12345?by=external_id
```

**Response (200):**
```json
{
  "customer_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1 416 555 1234",
  "phone_normalized": "+14165551234",
  "company": "Acme Corp",
  "external_crm_id": "CRM-12345",
  "created_at": "2026-01-15T10:00:00",
  "updated_at": "2026-02-20T10:30:00"
}
```

**Curl:**
```bash
curl -X GET "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/customers/123?by=id" \
  -H "x-api-key: YOUR_KEY"
```

---

#### 4. Update Customer

**When to use:** You need to change customer details (name, email, phone, company).

**Endpoint:** `PUT /customers/{customer_id}`

**Request:**
```json
{
  "name": "John Smith",
  "email": "john.smith@newexample.com",
  "company": "New Company Inc"
}
```

**Response (200):**
```json
{
  "customer_id": 123,
  "name": "John Smith",
  "email": "john.smith@newexample.com",
  ...
}
```

**Curl:**
```bash
curl -X PUT "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/customers/123" \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Smith","company":"New Company Inc"}'
```

---

#### 5. Delete Customer

**When to use:** Remove a customer from the CRM (rarely used - usually just archive).

**Endpoint:** `DELETE /customers/{customer_id}`

**Response (200):**
```json
{
  "success": true,
  "deleted_id": 123
}
```

**Curl:**
```bash
curl -X DELETE "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/customers/123" \
  -H "x-api-key: YOUR_KEY"
```

---

#### 6. Lookup Customer

**When to use:** You have an email or phone and want to find the customer - simpler than using GET with query params.

**Endpoint:** `POST /customers/lookup`

**Request:**
```json
{
  "phone": "+14165551234"
}
```
OR
```json
{
  "email": "john@example.com"
}
```

**Response (200):**
```json
{
  "customer_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  ...
}
```

**Response (404):** Customer not found

**Curl:**
```bash
curl -X POST "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/customers/lookup" \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"phone":"+14165551234"}'
```

---

#### 7. Upsert Customer

**When to use:** You want to create a customer if they don't exist, or update them if they do - all in one call. Requires email.

**Endpoint:** `POST /customers/upsert`

**Request:**
```json
{
  "email": "john@example.com",
  "name": "John Doe",
  "phone": "+14165551234",
  "company": "Acme Corp"
}
```

**Response (200/201):**
```json
{
  "customer": {
    "customer_id": 123,
    "name": "John Doe",
    ...
  },
  "created": true   // true = new customer created, false = existing customer returned
}
```

**Curl:**
```bash
curl -X POST "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/customers/upsert" \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","name":"John Doe","phone":"+14165551234"}'
```

---

### CONTEXT

---

#### 8. Get Conversation Context

**When to use:** A message arrives (SMS, email, etc.) and you want to know:
- Who is this customer?
- What's the conversation history?
- What's the current status (active, paused, resolved)?
- What was the last intent, sentiment, summary?

**This is your PRIMARY entry point** when processing any incoming message.

**Endpoint:** `GET /context/{identifier}?by=id|email|phone_normalized`

**Important:** Use `phone_normalized` (not `phone`) for phone lookups.

**Examples:**
```bash
# By customer ID
GET /context/123

# By email
GET /context/john%40example.com?by=email

# By phone (USE phone_normalized)
GET /context/%2B14165551234?by=phone_normalized
```

**Response - Existing Conversation (200):**
```json
{
  "context_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": 123,
  "customer": {
    "customer_id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+14165551234"
  },
  "status": "active",
  "summary": "Customer interested in enterprise pricing for 50-user team",
  "intent": "pricing_inquiry",
  "sentiment": "positive",
  "last_channel": "sms",
  "last_interaction_at": "2026-02-17T14:30:00",
  "message_count": 5,
  "open_questions": "What's your team size?",
  "last_agent_action": "Sent pricing PDF",
  "history": [
    {
      "direction": "inbound",
      "message_body": "I want enterprise pricing",
      "channel": "sms",
      "created_at": "2026-02-17T14:30:00"
    }
  ],
  "is_new": false
}
```

**Response - New Conversation (200):**
```json
{
  "context_id": null,
  "customer_id": 123,
  "customer": {...},
  "summary": "New conversation - no active/paused context",
  "history": [],
  "previous_conversations": [...],
  "is_new": true
}
```

**Response - Not Found (404):**
```json
{
  "error": "Customer not found with phone_normalized: +14165551234"
}
```

**Curl:**
```bash
curl -X GET "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/context/%2B14165551234?by=phone_normalized" \
  -H "x-api-key: YOUR_KEY"
```

---

#### 9. Update Conversation Context

**When to use:** After your AI/Brain processes a message and generates a response. You need to update:
- Summary of conversation
- Detected intent
- Sentiment
- Open questions
- What the agent did

**Endpoint:** `POST /context/{context_id}/update`

**Important:** URL is `/context/` NOT `/conversation/`

**Request:**
```json
{
  "summary": "Customer interested in enterprise plan pricing",
  "intent": "pricing_inquiry",
  "sentiment": "positive",
  "last_message_preview": "Customer asked about enterprise pricing",
  "last_channel": "sms",
  "open_questions": "What's your team size?",
  "last_agent_action": "Sent pricing information"
}
```

**All fields are optional** - include only what you want to update.

**Response (200):**
```json
{
  "success": true,
  "context_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": 123,
  "message_count": 6
}
```

**Curl:**
```bash
curl -X POST "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/context/550e8400-e29b-41d4-a716-446655440000/update" \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"summary":"Customer interested in pricing","intent":"pricing_inquiry","sentiment":"positive"}'
```

---

### MESSAGES / LOG

---

#### 10. Log a Message

**When to use:** Record any message (inbound from customer OR outbound to customer). This is how you build conversation history.

**Endpoint:** `POST /log`

**For inbound messages (from customer):**
```json
{
  "customer_id": 123,
  "channel": "sms",
  "channel_identifier": "+14165551234",
  "direction": "inbound",
  "message_body": "Hi, I need help with pricing"
}
```

**For outbound messages (to customer):**
```json
{
  "customer_id": 123,
  "channel": "sms",
  "channel_identifier": "+14165551234",
  "direction": "outbound",
  "message_body": "Hi! Our plans start at $99/month",
  "context_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Field descriptions:**
| Field | Required | Description |
|-------|----------|-------------|
| `customer_id` | Yes | Customer ID from /customers or /context |
| `channel` | Yes | `email`, `chat`, `voice`, `sms`, `whatsapp`, `social` |
| `channel_identifier` | Yes | Email, phone, or social handle |
| `direction` | Yes | `inbound` (from customer) or `outbound` (to customer) |
| `message_body` | Yes | The message content |
| `message_subject` | No | Subject line (for email) |
| `context_id` | No | Conversation ID. If omitted, uses existing active or creates new |
| `metadata` | No | Any extra data (Twilio SID, etc.) |
| `send_status` | No | `sent`, `pending`, `failed` (default: sent) |

**Response (200):**
```json
{
  "success": true,
  "log_id": 789,
  "context_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Curl:**
```bash
curl -X POST "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod/log" \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":123,"channel":"sms","channel_identifier":"+14165551234","direction":"inbound","message_body":"Hi, I need help"}'
```

---

#### 11. List/Search Messages

**When to use:** Find messages with filters.

**Endpoint:** `GET /messages`

**Query Parameters:**
| Param | Description |
|-------|-------------|
| `channel` | Filter by channel (sms, email, etc.) |
| `direction` | Filter by direction (inbound, outbound) |
| `limit` | Number of results |
| `offset` | Pagination |

**Response (200):**
```json
{
  "messages": [
    {
      "log_id": 789,
      "context_id": "...",
      "customer_id": 123,
      "channel": "sms",
      "direction": "inbound",
      "message_body": "Hi",
      "created_at": "2026-02-20T10:00:00"
    }
  ],
  "count": 1
}
```

---

#### 12. Get Message by ID

**When to use:** You have a specific log_id and want the full message details.

**Endpoint:** `GET /messages/{log_id}`

**Response (200):**
```json
{
  "log_id": 789,
  "context_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": 123,
  "channel": "sms",
  "channel_identifier": "+14165551234",
  "direction": "inbound",
  "message_body": "Hi, I need help",
  "message_subject": null,
  "metadata": {"twilio_message_sid": "SM123456"},
  "processed": false,
  "send_status": "sent",
  "created_at": "2026-02-20T10:00:00"
}
```

---

#### 13. Get Messages for a Conversation

**When to use:** You have a context_id and want all messages in that conversation.

**Endpoint:** `GET /messages/context/{context_id}`

**Response (200):**
```json
{
  "messages": [
    {"log_id": 1, "direction": "inbound", "message_body": "Hi", ...},
    {"log_id": 2, "direction": "outbound", "message_body": "Hello!", ...},
    {"log_id": 3, "direction": "inbound", "message_body": "Pricing?", ...}
  ],
  "count": 3
}
```

---

#### 14. Get Messages for a Customer

**When to use:** You have a customer_id and want ALL their messages across all conversations.

**Endpoint:** `GET /messages/customer/{customer_id}`

---

#### 15. Update Message Status

**When to use:** Update delivery status (e.g., after Twilio callback confirms delivery or failure).

**Endpoint:** `PUT /messages/{log_id}/status`

**Request:**
```json
{
  "send_status": "delivered"
}
```

Valid values: `sent`, `delivered`, `failed`, `pending`

**Response (200):**
```json
{
  "success": true,
  "log_id": 789,
  "send_status": "delivered"
}
```

---

#### 16. Mark Message as Processed

**When to use:** Mark a single message as processed (already handled by AI/Brain).

**Endpoint:** `POST /messages/{log_id}/processed`

**Response (200):**
```json
{
  "success": true,
  "log_id": 789
}
```

---

#### 17. Mark All Messages in Conversation as Processed

**When to use:** Mark all unprocessed messages in a conversation as processed at once.

**Endpoint:** `POST /messages/context/{context_id}/processed`

**Response (200):**
```json
{
  "success": true,
  "context_id": "...",
  "updated_count": 5
}
```

---

#### 18. Get Unprocessed Messages

**When to use:** Find all messages that haven't been processed yet (for batch processing).

**Endpoint:** `GET /messages/unprocessed`

**Response (200):**
```json
{
  "messages": [
    {"log_id": 789, "message_body": "New inquiry", ...}
  ],
  "count": 1
}
```

---

#### 19. Get Failed Messages

**When to use:** Find all messages that failed to send (for retry logic).

**Endpoint:** `GET /messages/failed`

---

### CONVERSATIONS

---

#### 20. List/Search Conversations

**When to use:** Find conversations with filters.

**Endpoint:** `GET /conversations`

**Query Parameters:**
| Param | Description |
|-------|-------------|
| `status` | Filter by status (active, paused, resolved, archived) |
| `customer_id` | Filter by customer |
| `limit` | Number of results |
| `offset` | Pagination |

**Response (200):**
```json
{
  "conversations": [
    {
      "context_id": "550e8400-e29b-41d4-a716-446655440000",
      "customer_id": 123,
      "status": "active",
      "message_count": 5,
      "last_interaction_at": "2026-02-20T10:00:00"
    }
  ],
  "count": 1
}
```

---

#### 21. Get Conversation by ID

**When to use:** You have a context_id and want full conversation details.

**Endpoint:** `GET /conversations/{context_id}`

---

#### 22. Get Active Conversation for Customer

**When to use:** Find the current active conversation for a specific customer.

**Endpoint:** `GET /conversations/customer/{customer_id}`

**Response (200):**
```json
{
  "context_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": 123,
  "status": "active",
  ...
}
```

**Response (404):** No active conversation found

---

#### 23. Create Conversation

**When to use:** Manually create a new conversation (usually handled automatically by /log).

**Endpoint:** `POST /conversations`

**Request:**
```json
{
  "customer_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+14165551234"
}
```

---

#### 24. Update Conversation

**When to use:** Update conversation fields directly.

**Endpoint:** `PUT /conversations/{context_id}`

**Request:**
```json
{
  "status": "paused",
  "conversation_summary": "Customer requested callback"
}
```

---

#### 25. Close/Resolve/Archive Conversation

**When to use:** Mark a conversation as resolved (success), archived (dead lead), or paused (follow up later).

**Endpoint:** `POST /conversations/{context_id}/close`

**Request:**
```json
{
  "status": "resolved"
}
```

Valid values: `resolved`, `archived`, `paused`

---

#### 26. Get or Create Conversation

**When to use:** Get existing active conversation OR create a new one if none exists - in one call.

**Endpoint:** `POST /conversations/get-or-create`

**Request:**
```json
{
  "customer_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+14165551234"
}
```

**Response (200):**
```json
{
  "context_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": 123,
  "status": "active",
  "created": false   // true = new conversation, false = existing
}
```

---

## Common Workflows

### Workflow 1: Handle Incoming SMS (Known Customer)

```
1. GET /context/{phone}?by=phone_normalized
   → Returns customer_id, context_id, history

2. POST /log (inbound)
   → Records the customer's message

3. [AI/Brain processes message]

4. POST /log (outbound)
   → Records your response

5. POST /context/{context_id}/update
   → Updates summary, intent, sentiment
```

### Workflow 2: Handle Incoming SMS (Unknown Phone Number)

```
1. GET /context/{phone}?by=phone_normalized
   → Returns 404 (customer not found)

2. POST /customers
   → Creates new customer with phone number

3. GET /context/{phone}?by=phone_normalized
   → Now returns the new customer

4. POST /log (inbound)
   → Records the message

5. [AI/Brain processes message]

6. POST /log (outbound)
   → Records your response

7. POST /context/{context_id}/update
   → Updates conversation state
```

---

## Channel Values

Use these values for the `channel` field:

| Channel | Value |
|---------|-------|
| Email | `email` |
| Chat/Chatbot | `chat` |
| Voice/Phone | `voice` |
| SMS | `sms` |
| WhatsApp | `whatsapp` |
| Social Media | `social` |

---

## Conversation Status Values

| Status | Meaning |
|--------|---------|
| `active` | Ongoing conversation |
| `paused` | Cold lead, follow up later |
| `resolved` | Successfully converted |
| `archived` | Dead lead, no further action |

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request - check your JSON |
| 404 | Not found |
| 500 | Server error |

---

## Support

For questions or issues, check:
1. CloudWatch logs: `/aws/lambda/{function_name}`
2. Verify API key is correct
3. Verify JSON is valid
