# Tasks: Scheduled follow-ups
# Uses `rq` worker to send messages after a delay

from rq import Queue
import os
import redis
from twilio.rest import Client
from utils import log_event
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.Redis.from_url(redis_url)
q = Queue(connection=redis_client)

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def schedule_follow_up(phone_number, campaign_step):
    """
    Sends a follow-up SMS after the scheduled delay.
    Checks Redis first to see if user has replied (stop follow-ups).
    """
    
    # Check if we should cancel (user replied or DND)
    if redis_client.get(f"stop_campaign:{phone_number}") or redis_client.get(f"dnd:{phone_number}"):
        log_event(f"Skipping {campaign_step} for {phone_number} (replied or DND)")
        return

    # Campaign logic
    message_body = ""
    next_step = None
    next_delay = None

    if campaign_step == 'follow_up_1':
        message_body = "Hi there! Just checking if you saw my last message regarding the property? Let me know if you have questions. - {{AGENT_NAME}}"
        next_step = 'follow_up_2'
        next_delay = 86400  # 24 hours

    elif campaign_step == 'follow_up_2':
        message_body = "Hey again! Are you still interested in buying/selling? If not, just reply 'stop' and I won't bug you. Thanks!"
        next_step = None # End of sequence
    
    if message_body:
        # Send SMS via Twilio
        try:
            message = client.messages.create(
                body=message_body.replace('{{AGENT_NAME}}', os.getenv('AGENT_NAME', 'Wonderbot')),
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            log_event(f"Sent {campaign_step} to {phone_number}: {message.sid}")
            
            # Schedule next step if applicable
            if next_step and next_delay:
                q.enqueue_in(timedelta(seconds=next_delay), schedule_follow_up, phone_number, next_step)
                
        except Exception as e:
            log_event(f"Failed to send SMS to {phone_number}: {str(e)}")
