import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sarah_db_client import SarahDBClient
from twilio.rest import Client
import requests

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("CORE_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
AGENT_NAME = os.getenv("AGENT_NAME", "Wonderbot")

# Initialize Clients
db_client = SarahDBClient(api_key=API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Thresholds
THRESHOLD_FOLLOWUP_1_MINS = 30
THRESHOLD_FOLLOWUP_2_HOURS = 24

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
        hours_since_last = time_diff.total_seconds() / 3600

        # Get phone number (prefer normalized)
        customer_data = context.get("customer", {})
        phone = customer_data.get("phone_normalized") or customer_data.get("phone")
        
        # Logic: WAITING_FOR_ANSWER -> FOLLOWUP_1
        if intent == "WAITING_FOR_ANSWER" and mins_since_last >= THRESHOLD_FOLLOWUP_1_MINS:
            print(f"⚡ Triggering Follow-up #1 for {context_id}")
            msg_body = f"Hi {customer_data.get('name', 'there')}, just bumping this up! Did you have any thoughts on my last message? - {AGENT_NAME}"
            
            sid = send_sms(phone, msg_body)
            if sid:
                db_client.log_message(
                    customer_id=customer_id,
                    channel="sms",
                    identifier=phone,
                    direction="outbound",
                    body=msg_body,
                    context_id=context_id,
                    metadata={"twilio_sid": sid, "type": "auto_followup_1"}
                )
                db_client.update_conversation(customer_id=customer_id, intent="FOLLOWUP_1", summary=f"Auto-sent Follow-up #1")

        # Logic: FOLLOWUP_1 -> FOLLOWUP_2
        elif intent == "FOLLOWUP_1" and hours_since_last >= THRESHOLD_FOLLOWUP_2_HOURS:
            print(f"⚡ Triggering Follow-up #2 for {context_id}")
            msg_body = f"Hey again! Are you still interested? If not, reply 'stop'. Thanks! - {AGENT_NAME}"
            
            sid = send_sms(phone, msg_body)
            if sid:
                db_client.log_message(
                    customer_id=customer_id,
                    channel="sms",
                    identifier=phone,
                    direction="outbound",
                    body=msg_body,
                    context_id=context_id,
                    metadata={"twilio_sid": sid, "type": "auto_followup_2"}
                )
                db_client.update_conversation(customer_id=customer_id, intent="FOLLOWUP_2", summary=f"Auto-sent Follow-up #2")

        # Logic: FOLLOWUP_2 -> NURTURE
        elif intent == "FOLLOWUP_2" and hours_since_last >= THRESHOLD_FOLLOWUP_2_HOURS:
            print(f"💤 Moving {context_id} to NURTURE")
            db_client.update_conversation(customer_id=customer_id, intent="NURTURE", summary="Moved to Nurture (unresponsive)")

if __name__ == "__main__":
    process_conversations()
