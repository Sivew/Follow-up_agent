from flask import Flask, request, jsonify
from flask_redis import FlaskRedis
from rq import Queue
import json
import os
import openai
import logging
import redis
import textwrap
from twilio.twiml.messaging_response import MessagingResponse
from utils import log_event
from dotenv import load_dotenv
from sarah_db_client import SarahDBClient

# Initialize basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Redis & RQ for scheduling follow-ups
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['REDIS_URL'] = redis_url
redis_client = FlaskRedis(app)
q = Queue(connection=redis.Redis.from_url(redis_url))

# Configuration
CORE_API_KEY = os.getenv('CORE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.2')
MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')

if not CORE_API_KEY:
    logger.error("CORE_API_KEY is missing!")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is missing!")
if not MAKE_WEBHOOK_URL:
    logger.warning("MAKE_WEBHOOK_URL is missing - calendar booking will not work!")

# Initialize Clients
openai.api_key = OPENAI_API_KEY
db_client = SarahDBClient(api_key=CORE_API_KEY)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "follow-up-agent"}), 200

def generate_smart_reply(context_data, user_input):
    """
    Generate a 'Wonderbot-style' context-aware reply using all available DB columns.
    """
    # 1. Extract Rich Context Variables
    customer = context_data.get('customer', {})
    name = customer.get('name', 'there')
    summary = context_data.get('summary', 'New conversation')
    intent = context_data.get('intent', 'unknown')
    sentiment = context_data.get('sentiment', 'neutral')
    history = context_data.get('history', [])

    # 2. Format Recent History (Last 5 messages for flow)
    recent_dialogue = ""
    if history:
        for msg in reversed(history[:5]):
            role = "User" if msg['direction'] == 'inbound' else "Sarah"
            content = msg.get('message_body', '')
            recent_dialogue += f"{role}: {content}\n"

    # 3. Construct the 'Omniscient' Prompt
    system_prompt = f"""
You are Sarah, an AI consultant for **Kalkia Évolution IA** — we help businesses automate and scale using AI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 YOUR DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- **Lead Name:** {name}
- **Current Stage:** {intent}
- **Sentiment:** {sentiment}
- **Conversation Summary:** "{summary}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Goal:** Qualify leads and get them on a call. You succeed when you book a consultation OR get permission to call them.

**Strategy:** DISCOVER → QUALIFY → ESCALATE

1. **DISCOVER** (if you don't know yet):
   - What's their business or role?
   - What problem are they trying to solve?

2. **QUALIFY** (gauge fit & urgency):
   - Are they exploring or actively looking for a solution?
   - Do they have a timeline? ("soon", "this quarter", "just researching")
   - Are they the decision-maker or gathering info for someone?

3. **ESCALATE** (based on interest signals):
   - **Warm signals:** Asks questions, engages positively, mentions a problem
     → Proactively suggest: "Would a quick 5-min call be easier? I can explain more clearly over the phone."
   - **Hot signals:** Asks about pricing, timeline, implementation, or says they're "ready"
     → Offer immediate call: "Want me to call you right now? I can answer everything in 2 minutes."
   - If they agree to a call → ask "What's a good time? I can call you in the next few minutes, or we can schedule."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠️ WHAT WE OFFER (match to their need)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **AI Receptionist** – Bilingual, books appointments, takes orders, sends confirmations
2. **AI Sales Agents** – Makes calls to close deals or capture leads
3. **AI Chatbots** – Website or business ecosystem integration
4. **Custom Automation Agents** – Tailored workflows for business processes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 BOOKING FLOW (when they want to schedule)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. If they mention a day/time → call `get_availability` immediately (don't reply first)
2. If slot is open → confirm and ask for their email (you have their phone)
3. Once you have email → call `book_appointment` to finalize
⚠️ NEVER say "booked" unless `book_appointment` succeeded.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 COMMUNICATION STYLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- **Language:** Match the user (English or Quebec French)
- **Tone:** Warm, consultative, confident — NOT robotic or salesy
- **Length:** Keep messages short (2-3 sentences max for SMS)
- **Be proactive:** Don't wait for them to ask to book — if they're interested, suggest it

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 AVOID
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Don't over-explain products in text — save details for the call
- Don't ask multiple questions at once — one question per message
- Don't say you can't check calendar — you CAN via `get_availability`
- After booking confirmed, don't ask more questions — just confirm & thank them
    """

    messages = [{"role": "system", "content": system_prompt}]
    
    # 2.5 Inject true message history so OpenAI natively understands its function call role
    if history:
        for msg in reversed(history[:8]):
            role = "user" if msg['direction'] == 'inbound' else "assistant"
            content = msg.get('message_body', '')
            messages.append({"role": role, "content": content})
            
    messages.append({"role": "user", "content": user_input})

    functions = [
        {
            "name": "get_availability",
            "description": "Call this ALWAYS when the user suggests a day or time for an appointment, to check if it is free.",
            "parameters": {
                "type": "object",
                "properties": {
                    "datetime_string": {
                        "type": "string",
                        "description": "The date and time the user wants (e.g., 'Tomorrow at 2pm', 'Next Tuesday morning')."
                    }
                },
                "required": ["datetime_string"]
            }
        },
        {
            "name": "book_appointment",
            "description": "Call this ONLY after the user has confirmed a specific time slot and provided their phone and email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "datetime_string": {
                        "type": "string",
                        "description": "The exact confirmed date and time to book."
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "The user's confirmed phone number."
                    },
                    "email": {
                        "type": "string",
                        "description": "The user's confirmed email address."
                    }
                },
                "required": ["datetime_string", "phone_number", "email"]
            }
        }
    ]

    try:
        print("DEBUG: Generating Smart Reply...")
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages,
            functions=functions,
            function_call="auto",
            max_tokens=300,
            temperature=0.7 
        )
        
        response_message = completion.choices[0].message
        
        # Check if the model wants to call the webhook function
        if response_message.get("function_call"):
            func_name = response_message["function_call"]["name"]
            try:
                func_args = json.loads(response_message["function_call"]["arguments"])
            except:
                func_args = {}
                
            if func_name in ["get_availability", "book_appointment"]:
                print(f"DEBUG: AI calling {func_name}: {func_args}")
                
                # Make the Webhook Call (Matching Vapi Structure for Make.com)
                webhook_payload = {
                    "message": {
                        "type": "tool_calls",
                        "toolCalls": [
                            {
                                "id": "call_" + str(context_data.get('customer_id', 'sms')),
                                "type": "function",
                                "function": {
                                    "name": func_name,
                                    "arguments": json.dumps(func_args)
                                }
                            }
                        ]
                    },
                    "customer_data": {
                        "phone": customer.get("phone_normalized", "unknown"),
                        "name": name,
                        "email": customer.get("email", ""),
                        "customer_id": context_data.get('customer_id'),
                        "context_id": context_data.get('context_id')
                    }
                }
                
                if not MAKE_WEBHOOK_URL:
                    function_result = '{"status": "error", "message": "MAKE_WEBHOOK_URL environment variable not configured"}'
                    print(f"❌ {function_result}")
                else:
                    try:
                        import requests
                        wh_resp = requests.post(MAKE_WEBHOOK_URL, json=webhook_payload, timeout=10)
                        function_result = wh_resp.text if wh_resp.text else '{"status": "success", "message": "Request processed but no text returned."}'
                        print(f"DEBUG: Webhook response: {function_result}")
                    except Exception as e:
                        function_result = f'{{"status": "error", "message": "Make.com Webhook timeout/error: {e}"}}'
                        print(function_result)

                # Send the webhook's response back to the LLM
                messages.append(response_message)
                messages.append({
                    "role": "function",
                    "name": func_name,
                    "content": function_result
                })
                
                print("DEBUG: Asking LLM to interpret the webhook result and reply to user...")
                second_completion = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7
                )
                return second_completion.choices[0].message.content.strip()

        # If no function was called, just return the normal text reply
        return response_message.content.strip()
        
    except Exception as e:
        print(f"DEBUG: OpenAI Reply Error: {e}")
        return "I'm analyzing that... one moment."

def update_conversation_state(old_summary, history, user_input, ai_reply):
    """
    Update Summary AND Sentiment based on the exchange.
    Returns a dict with {summary, sentiment, extracted_name, extracted_email, booking_requested, interest_level, product_interest, call_recommended}
    """
    prompt = f"""
Analyze this conversation exchange and update the CRM records.

**Context:**
- Old Summary: "{old_summary}"
- User Message: "{user_input}"
- Sarah's Reply: "{ai_reply}"

**Task:** Return a JSON object with these fields:

1. "summary": Updated concise summary (include what product/problem they discussed)

2. "sentiment": User's emotional state
   - "positive" = engaged, interested, friendly
   - "neutral" = just responding, unclear intent
   - "negative" = frustrated, annoyed, objecting
   - "confused" = unclear, asking for clarification

3. "extracted_name": User's name if mentioned (e.g., "I'm Shiva" → "Shiva"), else null

4. "extracted_email": User's email if provided, else null

5. "booking_requested": true ONLY if user explicitly asks to book/schedule/get a callback

6. "interest_level": Assess their buying intent
   - "hot" = mentions timeline, asks about pricing, says they're ready, wants to talk now
   - "warm" = asks questions, engages positively, describes a problem they have
   - "cold" = short replies, seems uninterested, just browsing

7. "product_interest": Which product they seem most interested in (or null):
   - "ai_receptionist"
   - "ai_sales_agent"
   - "ai_chatbot"
   - "custom_automation"
   - null (if unclear)

8. "call_recommended": true if Sarah should offer to call them NOW based on:
   - They asked multiple questions
   - They described a specific pain point
   - Sentiment is positive and they're engaged
   - They asked about pricing or timeline

Return raw JSON only (no markdown formatting).
    """

    try:
        print("DEBUG: Updating State...")
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.3
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Try to parse the JSON string to extract the actual fields
        try:
            # Handle potential markdown code blocks like ```json ... ```
            if response_text.startswith("```json") and response_text.endswith("```"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```") and response_text.endswith("```"):
                response_text = response_text[3:-3].strip()
                
            parsed_data = json.loads(response_text)
            
            # Extract fields
            summary_text = parsed_data.get("summary", old_summary)
            sentiment_val = parsed_data.get("sentiment", "neutral")
            
            return {
                "summary": summary_text,
                "sentiment": sentiment_val,
                "extracted_name": parsed_data.get("extracted_name"),
                "extracted_email": parsed_data.get("extracted_email"),
                "booking_requested": parsed_data.get("booking_requested", False),
                "interest_level": parsed_data.get("interest_level", "cold"),
                "product_interest": parsed_data.get("product_interest"),
                "call_recommended": parsed_data.get("call_recommended", False)
            }
        except json.JSONDecodeError:
            print(f"DEBUG: Failed to parse JSON from AI: {response_text}")
            # Fallback: Just return the raw text as summary if it wasn't valid JSON
            return {
                "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "sentiment": "neutral",
                "extracted_name": None,
                "extracted_email": None,
                "booking_requested": False
            }
            
    except Exception as e:
        print(f"DEBUG: OpenAI State Update Error: {e}")
        return {
            "summary": old_summary,
            "sentiment": "neutral"
        }

@app.route('/sms/inbound', methods=['POST'])
def handle_incoming_sms():
    sender = request.form.get('From')
    body = request.form.get('Body', '').strip()
    
    print(f"DEBUG: Received SMS from {sender}: {body}")
    log_event(f"Received SMS from {sender}: {body}")

    customer_id = None
    context_id = None
    context_data = {}

    # 1. Get Context
    try:
        try:
            context_data = db_client.get_context(identifier=sender, lookup_by="phone_normalized")
        except Exception as e:
            if "404" in str(e):
                print(f"DEBUG: Creating Customer...")
                try:
                    new_cust = db_client.create_customer(phone=sender, phone_normalized=sender)
                    customer_id = new_cust.get('customer_id')
                    context_data = db_client.get_context(identifier=sender, lookup_by="phone_normalized")
                except:
                    return str(MessagingResponse())
            else:
                raise e

        customer_id = context_data.get('customer_id')
        context_id = context_data.get('context_id') 
        
        # 2. Log Inbound
        log_resp = db_client.log_message(
            customer_id=customer_id,
            channel="sms",
            identifier=sender,
            direction="inbound",
            body=body,
            context_id=context_id
        )
        if not context_id:
            context_id = log_resp.get('context_id')

    except Exception as e:
        print(f"DEBUG: API Error: {e}")
        return str(MessagingResponse())

    # 3. Brain (Stop/Handoff)
    normalized_body = body.upper()
    if normalized_body in ["STOP", "CANCEL", "UNSUBSCRIBE"]:
        resp = MessagingResponse()
        return str(resp)

    if any(k in normalized_body for k in ["HUMAN", "CALL ME"]):
        reply_text = "I've noted your request. A member of our team will call you shortly."
        resp = MessagingResponse()
        resp.message(reply_text)
        try:
            db_client.log_message(customer_id, "sms", sender, "outbound", reply_text, context_id)
            db_client.update_conversation(context_id, last_agent_action="Handoff Requested")
        except: pass
        return str(resp)

    # 4. Generate Smart Reply (Full Context)
    reply_text = generate_smart_reply(context_data, body)
    print(f"DEBUG: Generated Reply: {reply_text}")

    # 5. Outbound Log & State Update
    try:
        db_client.log_message(
            customer_id=customer_id,
            channel="sms",
            identifier=sender,
            direction="outbound",
            body=reply_text,
            context_id=context_id
        )
    except Exception as e:
        print(f"DEBUG: Failed to log outbound message: {e}")

    try:
        history = context_data.get('history', [])
        current_summary = context_data.get('summary', '')
        
        # Get AI analysis (dictionary)
        state_updates = update_conversation_state(current_summary, history, body, reply_text)
        
        # Decide the new intent based on booking request or interest level
        # If booking is requested, flag as HOT_LEAD to stop follow-up cron loops!
        is_booking_req = state_updates.get("booking_requested", False)
        interest_level = state_updates.get("interest_level", "cold")
        call_recommended = state_updates.get("call_recommended", False)
        
        # Mark as HOT_LEAD if booking requested OR if they're hot and call is recommended
        if is_booking_req or (interest_level == "hot" and call_recommended):
            new_intent = "HOT_LEAD"
        else:
            new_intent = "WAITING_FOR_ANSWER"

        # Update DB:
        db_client.update_conversation(
            context_id=context_id,
            summary=state_updates.get("summary", current_summary),
            sentiment=state_updates.get("sentiment", "neutral"),
            intent=new_intent, 
            last_agent_action="AI Replied via SMS"
        )
        
        # Store new fields in conversation metadata (for future use)
        try:
            # You can extend the DB schema later to store these fields
            # For now, we'll log them for visibility
            print(f"DEBUG: Interest Level: {interest_level}, Product Interest: {state_updates.get('product_interest')}, Call Recommended: {call_recommended}")
        except Exception as meta_err:
            print(f"DEBUG: Failed to log metadata: {meta_err}")
        
        # 4. Update Customer if new info found
        ext_name = state_updates.get("extracted_name")
        ext_email = state_updates.get("extracted_email")
        product_interest = state_updates.get("product_interest")
        
        if ext_name or ext_email:
            print(f"DEBUG: Found new customer info - Name: {ext_name}, Email: {ext_email}")
            try:
                db_client.update_customer(customer_id=customer_id, name=ext_name, email=ext_email)
            except Exception as ce:
                print(f"DEBUG: Failed to update customer profile: {ce}")
        
        # 5. Voice Call Trigger Logic (VAPI Integration)
        # TODO: Implement VAPI call trigger when conditions are met
        # Trigger conditions:
        # - call_recommended == True (AI detected strong engagement)
        # - interest_level == "hot" (mentions timeline, pricing, ready to talk)
        # - User agrees to a call offer in the conversation
        #
        # Implementation steps:
        # 1. Add VAPI_WEBHOOK_URL to .env file
        # 2. Create a trigger_vapi_call() helper function that:
        #    - Calls VAPI API to initiate outbound call
        #    - Passes customer context (name, summary, product_interest)
        # 3. Uncomment the logic below:
        #
        # if call_recommended and interest_level in ["warm", "hot"]:
        #     # Check if we've already offered a call in this conversation
        #     already_offered = any("call you" in msg.get("message_body", "").lower() 
        #                          for msg in history[-3:] if msg.get("direction") == "outbound")
        #     
        #     if not already_offered:
        #         # VAPI will be triggered when user responds "yes" to Sarah's call offer
        #         # Sarah's prompt already includes language to offer calls proactively
        #         print(f"DEBUG: Call recommended for {ext_name or 'customer'} - Sarah should offer call")
                
    except Exception as e:
        print(f"DEBUG: Failed to update conversation context: {e}")

    # 6. Response Construction (Smart Splitting)
    # Always build and return response - don't let DB errors prevent SMS delivery
    resp = MessagingResponse()
    
    # Split message if > 160 chars to avoid carrier truncation issues
    # Ideally keep under 1600 total (Twilio limit), but split into 160-char chunks for delivery order
    # Using 320 to allow slightly longer cohesive thoughts per bubble if carrier supports concatenation
    # But for safety and UX, 160-200 is a good visual breakpoint.
    
    # NOTE: textwrap.wrap returns a list of strings
    chunks = textwrap.wrap(reply_text, width=300, break_long_words=False, replace_whitespace=False)
    
    for chunk in chunks:
        resp.message(chunk)
        
    return str(resp)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
