from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
from sarah_db_client import SarahDBClient

load_dotenv()

app = Flask(__name__)

# Configuration (from .env)
API_BASE_URL = os.getenv("CORE_API_URL")
API_KEY = os.getenv("CORE_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Initialize Client
db_client = SarahDBClient(api_key=API_KEY)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "sms-automation"}), 200

@app.route('/sms/inbound', methods=['POST'])
def handle_incoming_sms():
    """
    Webhook for incoming SMS messages (e.g., from Twilio).
    1. Log to Core API
    2. Reset state to ENGAGED (stop auto-followups)
    """
    data = request.form
    sender = data.get('From')
    body = data.get('Body')
    
    if not sender or not body:
        return "Missing sender or body", 400

    try:
        # 1. Get Context (to find customer_id)
        # Note: API Guide says use phone_normalized for lookup
        # Twilio sends E.164 which is usually normalized (+1415...)
        context = db_client.get_context(sender, lookup_by="phone_normalized")
        customer_id = context.get('customer_id')
        context_id = context.get('context_id')

        if not customer_id:
            print(f"Unknown customer {sender}. Creating new customer...")
            # Create new customer if not found
            new_cust = db_client.create_customer(phone=sender, phone_normalized=sender)
            customer_id = new_cust.get('customer_id')

        # 2. Log Message
        log_resp = db_client.log_message(
            customer_id=customer_id,
            channel="sms",
            identifier=sender,
            direction="inbound",
            body=body,
            context_id=context_id
        )
        
        # 3. Update State -> ENGAGED
        # This stops the cron worker from sending follow-ups
        if context_id:
            db_client.update_conversation(
                customer_id=customer_id,
                intent="ENGAGED",
                summary=f"User replied: {body[:50]}..."
            )
            print(f"✅ Reset state to ENGAGED for context {context_id}")

    except Exception as e:
        print(f"❌ Error processing inbound SMS: {e}")
        return str(e), 500
    
    return "", 200  # Acknowledge receipt

@app.route('/sms/status', methods=['POST'])
def handle_sms_status():
    """
    Webhook for message status updates (sent, delivered, failed).
    """
    data = request.form
    message_sid = data.get('MessageSid')
    status = data.get('MessageStatus')
    
    # TODO: Update status in Core API
    
    return "", 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
