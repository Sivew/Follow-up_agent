# Make.com Setup - Action Items

## Calendar Integration Webhook

**Purpose:** Check availability & book appointments when AI detects booking intent.

### Actions Required:

1. **Create Webhook Receiver**
   - Add Custom Webhook module in Make.com
   - Copy webhook URL → Add to `.env` as `MAKE_WEBHOOK_URL`

2. **Configure Calendar Connection**
   - Connect to your calendar service (Google Calendar/Calendly/etc)
   - Set up availability check logic
   - Set up booking logic

3. **Handle Incoming Requests**
   - Parse JSON body: `action` field = "check_availability" or "book_appointment"
   - Extract: `customer_data.name`, `customer_data.email`, `customer_data.phone`
   - Extract: `requested_time` (if provided)

4. **Return Response Format**
   - For availability check:
     ```json
     {"results": ["Tuesday 2pm", "Wednesday 10am", "Thursday 3pm"]}
     ```
   - For booking:
     ```json
     {"status": "success", "confirmation": "Booked for Tuesday 2pm"}
     ```

**Critical:** Response MUST be raw JSON, not wrapped in HTTP envelope. Use "Respond to Webhook" module with JSON body.

---

## Voice AI Integration (Optional)

**Purpose:** Log Vapi voice calls to Sarah DB.

### Actions Required:

1. **Incoming Call Webhook**
   - Create webhook for Vapi incoming calls
   - Parse phone number from Vapi payload
   - Call: `GET /context/{phone}?by=phone_normalized`
   - Return customer data to Vapi for personalization

2. **Call Ended Webhook**
   - Create webhook for Vapi end-of-call
   - Extract: phone, duration, transcript
   - Call: `POST /log` with `channel: "voice"`
   - Call: `POST /conversation/{context_id}/update` with summary

3. **HTTP Module Configuration**
   - Method: GET or POST
   - URL: `${CORE_API_URL}/endpoint`
   - Authentication: **None**
   - Headers (manual):
     - `x-api-key: ${CORE_API_KEY}`
     - `Content-Type: application/json`

**Critical:** Don't use Authentication dropdown. Add `x-api-key` manually in Headers section.
