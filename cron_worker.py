import os
import time
import json
import openai
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sarah_db_client import SarahDBClient
from twilio.rest import Client
import requests

# Load environment variables
load_dotenv()

# Retry tracking
MAX_SMS_RETRIES = 3
RETRY_FILE = os.path.join(os.path.dirname(__file__), 'sms_retry_counts.json')

def load_retry_counts():
    try:
        with open(RETRY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_retry_counts(counts):
    with open(RETRY_FILE, 'w') as f:
        json.dump(counts, f, indent=2)

def get_retry_count(context_id):
    counts = load_retry_counts()
    return counts.get(context_id, 0)

def increment_retry(context_id):
    counts = load_retry_counts()
    counts[context_id] = counts.get(context_id, 0) + 1
    save_retry_counts(counts)
    return counts[context_id]

def clear_retry(context_id):
    counts = load_retry_counts()
    if context_id in counts:
        del counts[context_id]
        save_retry_counts(counts)

# Configuration
API_KEY = os.getenv("CORE_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
AGENT_NAME = os.getenv("AGENT_NAME", "Wonderbot")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
openai.api_key = OPENAI_API_KEY

# Initialize Clients
db_client = SarahDBClient(api_key=API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Load Strategy
STRATEGY_FILE = os.path.join(os.path.dirname(__file__), "followup_strategy.json")
with open(STRATEGY_FILE, "r") as f:
    STRATEGY = json.load(f)

def generate_smart_followup(context, instruction, customer_name):
    """Uses LLM to generate a contextual follow-up message."""
    history = context.get("history", [])
    recent_history = history[-4:] if len(history) >= 4 else history
    summary = context.get("summary", "No summary available.")
    product_interest = context.get("product_interest", "")
    
    # Add product context if available
    product_context = ""
    if product_interest:
        product_map = {
            "ai_receptionist": "AI Receptionist",
            "ai_sales_agent": "AI Sales Agents",
            "ai_chatbot": "AI Chatbots",
            "custom_automation": "Custom Automation Agents"
        }
        product_context = f"\n\nThey showed interest in: {product_map.get(product_interest, product_interest)}"
    
    prompt = f"""
You are {AGENT_NAME}, an AI assistant following up with a lead named {customer_name}.

Current conversation summary:
"{summary}"{product_context}

Recent message history:
{json.dumps(recent_history, indent=2)}

Task / Instruction for this follow-up:
{instruction}

Draft a short, natural, friendly SMS text message (max 160 chars) to send them right now. 
Make sure it feels like a natural continuation of the history.
Do NOT include quotes around the message. Just return the raw text.
    """
    try:
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        # Fallback message if LLM fails
        return f"Hi {customer_name}, just bumping this up! Did you have any thoughts on my last message? - {AGENT_NAME}"

def send_sms(to_number, body):
    """Sends SMS via Twilio and logs it to the DB."""
    try:
        if not to_number:
            print("❌ Cannot send SMS: No phone number provided")
            return None
            
        message = twilio_client.messages.create(
            body=body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        print(f"✅ Sent SMS to {to_number}: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"❌ Failed to send SMS to {to_number}: {e}")
        return None

def process_conversations():
    print(f"🔄 Running Worker at {datetime.now(timezone.utc)}")
    
    # 1. Fetch Customers (Workaround for missing /conversations endpoint)
    try:
        customers_resp = db_client.list_customers(limit=100)
        customers = customers_resp.get("customers", [])
    except Exception as e:
        print(f"Error fetching customers: {e}")
        return

    print(f"Found {len(customers)} customers. Checking contexts...")

    for cust in customers:
        customer_id = cust.get("customer_id")
        
        # 2. Fetch Context for each customer
        try:
            # Use string ID for lookup
            context = db_client.get_context(str(customer_id), lookup_by="id")
        except Exception as e:
            # print(f"Error getting context for {customer_id}: {e}")
            continue

        # Skip if no active context
        if context.get("status") != "active":
            continue
            
        intent = context.get("intent")
        last_interaction_str = context.get("last_interaction_at")
        context_id = context.get("context_id")
        
        if not intent or intent not in STRATEGY:
            continue

        if not last_interaction_str:
            continue

        # Parse timestamp
        try:
            last_interaction = datetime.fromisoformat(last_interaction_str.replace("Z", "+00:00"))
            if last_interaction.tzinfo is None:
                last_interaction = last_interaction.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        now = datetime.now(timezone.utc)
        time_diff = now - last_interaction
        mins_since_last = time_diff.total_seconds() / 60

        # Get Strategy Rules
        rule = STRATEGY[intent]
        wait_minutes = rule.get("wait_minutes")
        next_intent = rule.get("next_intent")
        instruction = rule.get("instruction")

        # Skip states that don't need auto-follow-ups
        if wait_minutes is None:
            continue

        if mins_since_last >= float(wait_minutes):
            print(f"⚡ Triggering rule {intent} -> {next_intent} for {context_id}")
            
            if instruction:
                # Personalize Template
                customer_data = context.get("customer", {})
                phone = customer_data.get("phone_normalized") or customer_data.get("phone")
                name = customer_data.get("name")
                if not name or name.lower() == "test user" or "unknown" in name.lower():
                    name = "there"

                print(f"DEBUG: Generating AI follow-up for {name}...")
                msg_body = generate_smart_followup(context, instruction, name)
                
                sid = send_sms(phone, msg_body)
                if sid:
                    db_client.log_message(
                        customer_id=customer_id,
                        channel="sms",
                        identifier=phone,
                        direction="outbound",
                        body=msg_body,
                        context_id=context_id,
                        metadata={"twilio_sid": sid, "type": f"auto_{next_intent.lower()}"}
                    )
                    
                    # Update summary dynamically to reflect the sent message
                    current_summary = context.get("summary", "")
                    updated_summary = f"{current_summary}\n\n[System Update] Sarah auto-sent follow-up: {msg_body[:40]}..."
                    
                    db_client.update_conversation(context_id=context_id, intent=next_intent, summary=updated_summary)
                    clear_retry(context_id)
                else:
                    # SMS failed - track retries
                    retries = increment_retry(context_id)
                    if retries >= MAX_SMS_RETRIES:
                        print(f"🚫 Max retries ({MAX_SMS_RETRIES}) reached for {context_id}. Moving to {next_intent} (SMS_FAILED).")
                        db_client.update_conversation(
                            context_id=context_id,
                            intent=next_intent,
                            summary=f"[SMS FAILED after {retries} attempts] Moved to {next_intent} - invalid or unreachable phone.",
                            last_agent_action=f"SMS delivery failed after {retries} retries"
                        )
                        clear_retry(context_id)
                    else:
                        print(f"⚠️ SMS failed for {context_id} (attempt {retries}/{MAX_SMS_RETRIES}). Will retry next cycle.")
            else:
                # No template means it's a silent phase transition (e.g. moving to NURTURE)
                print(f"💤 Moving {context_id} to {next_intent} (Silent)")
                db_client.update_conversation(context_id=context_id, intent=next_intent, summary=f"Moved to {next_intent} (unresponsive)")

if __name__ == "__main__":
    process_conversations()
