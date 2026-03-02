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
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

if not CORE_API_KEY:
    logger.error("CORE_API_KEY is missing!")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is missing!")

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
    You are Sarah, the intelligent AI partner for **Kalkia Évolution IA**.
    
    **YOUR DASHBOARD (CONTEXT):**
    - **Customer Name:** {name}
    - **Current Intent:** {intent}
    - **Sentiment:** {sentiment}
    - **Long-Term Memory:** "{summary}"
    
    **RECENT DIALOGUE (The Flow):**
    {recent_dialogue}
    
    **YOUR MISSION:**
    Engage naturally. You are NOT a script-reading robot. You are a consultant.
    - **Use the Dashboard:** If sentiment is 'frustrated', apologize. If intent is 'pricing', pivot to value.
    - **Use the Dialogue:** Reference specific things they just said. Match their vibe.
    - **Goal:** Explain our AI solutions (Receptionist, Sales Agents, Chatbots) and nudge for a **45-min consultation** when appropriate.

    **STYLE:**
    - Intriguing, Real, Professional but Warm.
    - **Anti-Robot:** Never repeat yourself word-for-word. If they ask the same thing twice, ask clarifying questions instead of repeating the answer.
    - Language: English or Quebec French (match user).
    
    **Handling "What is AI?" (if asked repeatedly):**
    - Don't just define it again. Ask: "Is there a specific part of the automation (like the booking or the follow-up) you're curious about?"
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    try:
        print("DEBUG: Generating Smart Reply...")
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=300, # INCREASED from 150 to prevent cutoffs
            temperature=0.7 
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"DEBUG: OpenAI Reply Error: {e}")
        return "I'm analyzing that... one moment."

def update_conversation_state(old_summary, history, user_input, ai_reply):
    """
    Update Summary AND Sentiment based on the exchange.
    Returns a dict with {summary, sentiment}
    """
    prompt = f"""
    Analyze this conversation exchange and update the CRM records.
    
    **Old Summary:** "{old_summary}"
    **User Input:** "{user_input}"
    **Sarah Reply:** "{ai_reply}"
    
    **Task:**
    Return a JSON object with 2 fields:
    1. "summary": Updated concise summary of the whole chat. Include the user's conversational intent (e.g., pricing_inquiry, technical_question) inside this text.
    2. "sentiment": User's emotional state (positive, neutral, negative, confused).
    
    Do NOT use Markdown formatting (like ```json). Just return the raw JSON braces.
    """

    try:
        print("DEBUG: Updating State...")
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
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
                "sentiment": sentiment_val
            }
        except json.JSONDecodeError:
            print(f"DEBUG: Failed to parse JSON from AI: {response_text}")
            # Fallback: Just return the raw text as summary if it wasn't valid JSON
            return {
                "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "sentiment": "neutral"
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
            db_client.update_conversation(customer_id, last_agent_action="Handoff Requested")
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

        # Update DB:
        # 1. Provide the new text summary
        # 2. Extract the sentiment to its dedicated column
        # 3. CRITICAL: Force `intent` = 'WAITING_FOR_ANSWER' so the cron worker will 
        #    trigger Follow-up #1 if user doesn't reply in 30 mins!
        db_client.update_conversation(
            customer_id=customer_id,
            summary=state_updates.get("summary", current_summary),
            sentiment=state_updates.get("sentiment", "neutral"),
            intent="WAITING_FOR_ANSWER", 
            last_agent_action="AI Replied via SMS"
        )
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
