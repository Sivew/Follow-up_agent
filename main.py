from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration (from .env)
API_BASE_URL = os.getenv("CORE_API_URL")
API_KEY = os.getenv("CORE_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "sms-automation"}), 200

@app.route('/sms/inbound', methods=['POST'])
def handle_incoming_sms():
    """
    Webhook for incoming SMS messages (e.g., from Twilio).
    1. Validate request (optional signature check)
    2. Extract sender, body
    3. Log to Core API
    4. Process logic (e.g., AI reply, escalation)
    5. Return TwiML or empty response
    """
    data = request.form
    sender = data.get('From')
    body = data.get('Body')
    
    # TODO: Implement core logic here
    # Example: response = process_message(sender, body)
    
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
