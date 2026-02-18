from flask import Flask, request, jsonify
from flask_redis import FlaskRedis
from rq import Queue
import os
import redis
import logging
from datetime import timedelta
from twilio.twiml.messaging_response import MessagingResponse
from utils import log_event, is_human_handoff_needed
from tasks import schedule_follow_up
from dotenv import load_dotenv

# Initialize basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Redis & RQ for scheduling follow-ups
# Redis URL: Use default localhost if not set
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['REDIS_URL'] = redis_url
redis_client = FlaskRedis(app)
q = Queue(connection=redis.Redis.from_url(redis_url))

# Configuration
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
FOLLOW_UP_DELAY_SECONDS = int(os.getenv('FOLLOW_UP_DELAY_SECONDS', 600))  # 10 minutes default

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "follow-up-agent"}), 200

@app.route('/sms/inbound', methods=['POST'])
def handle_incoming_sms():
    """
    Webhook for incoming SMS messages (e.g., from Twilio).
    """
    sender = request.form.get('From')
    body = request.form.get('Body', '').strip()
    
    log_event(f"Received SMS from {sender}: {body}")

    # 1. Check for STOP/UNSUBSCRIBE keywords
    if body.lower() in ['stop', 'unsubscribe', 'cancel']:
        redis_client.set(f"dnd:{sender}", "true")
        resp = MessagingResponse()
        resp.message("You have been unsubscribed. Reply START to resubscribe.")
        return str(resp)
    
    # 2. Check for human handoff (e.g. "call me", "agent")
    if is_human_handoff_needed(body):
        log_event(f"Human intervention needed for {sender}")
        # Stop automated follow-ups for this user
        redis_client.set(f"stop_campaign:{sender}", "true")
        # Notify human (Email/Slack/SMS to owner) - TODO
        resp = MessagingResponse()
        # No auto-reply, or a simple "Agent will contact you shortly"
        return str(resp)

    # 3. Process logic: If new lead or existing conversation
    # For now, simple auto-reply and schedule a follow-up
    resp = MessagingResponse()
    
    # If not in active conversation or DND
    if not redis_client.exists(f"active_conversation:{sender}") and not redis_client.exists(f"dnd:{sender}"):
        # First contact logic (New Lead or Cold Lead)
        resp.message("Thanks for reaching out! A member of our team will be with you shortly. (Automated Reply)")
        
        # Schedule a follow-up if they don't reply within X minutes
        # We store job ID if we want to cancel specifically later, but for now simple queue is OK
        q.enqueue_in(timedelta(seconds=FOLLOW_UP_DELAY_SECONDS), schedule_follow_up, sender, 'follow_up_1')
        
        # Mark as active conversation so we don't trigger "First Contact" again immediately
        redis_client.setex(f"active_conversation:{sender}", 3600, "active") # 1 hour expiry
    else:
        # Continuing conversation - Do nothing or reply?
        # Maybe use AI to generate a reply here later?
        # For now, we assume human agent might step in via dashboard if it's active
        pass

    return str(resp)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
