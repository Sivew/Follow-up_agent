"""
VAPI Outbound Call Trigger for Sarah Follow-up Agent.
Handles business hours checks, call scheduling, and VAPI API integration.
"""

import os
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")

# Business hours config
BUSINESS_TZ = ZoneInfo(os.getenv("BUSINESS_TIMEZONE", "America/Toronto"))
BUSINESS_HOUR_START = int(os.getenv("BUSINESS_HOUR_START", "9"))   # 9 AM
BUSINESS_HOUR_END = int(os.getenv("BUSINESS_HOUR_END", "20"))     # 8 PM
BUSINESS_DAYS = [0, 1, 2, 3, 4]  # Monday=0 through Friday=4


def is_business_hours(now=None):
    """Check if current time is within business hours (America/Toronto)."""
    if now is None:
        now = datetime.now(BUSINESS_TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc).astimezone(BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)

    return (now.weekday() in BUSINESS_DAYS and 
            BUSINESS_HOUR_START <= now.hour < BUSINESS_HOUR_END)


def next_business_window(now=None):
    """
    Returns the next available business hours datetime as a string.
    Example: 'tomorrow at 9:00 AM' or 'Monday at 9:00 AM'
    """
    if now is None:
        now = datetime.now(BUSINESS_TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc).astimezone(BUSINESS_TZ)
    else:
        now = now.astimezone(BUSINESS_TZ)

    candidate = now.replace(hour=BUSINESS_HOUR_START, minute=0, second=0, microsecond=0)

    # If we're before business hours today and it's a business day, use today
    if now.hour < BUSINESS_HOUR_START and now.weekday() in BUSINESS_DAYS:
        next_open = candidate
    else:
        # Move to next day
        candidate += timedelta(days=1)
        # Skip weekends
        while candidate.weekday() not in BUSINESS_DAYS:
            candidate += timedelta(days=1)
        next_open = candidate

    # Format friendly string
    days_ahead = (next_open.date() - now.date()).days
    if days_ahead == 0:
        day_str = "today"
    elif days_ahead == 1:
        day_str = "tomorrow"
    else:
        day_str = next_open.strftime("%A")  # e.g., "Monday"

    time_str = next_open.strftime("%-I:%M %p")  # e.g., "9:00 AM"
    return {
        "datetime": next_open.isoformat(),
        "friendly": f"{day_str} at {time_str}",
        "day_str": day_str,
        "time_str": time_str
    }


def trigger_vapi_call(phone, customer_name, summary, product_interest=None, interest_level="warm"):
    """
    Trigger an outbound VAPI call to a lead.
    Returns dict with call_id and status, or error info.
    """
    if not VAPI_API_KEY:
        print("❌ VAPI_API_KEY not configured")
        return {"success": False, "error": "VAPI_API_KEY not set"}
    
    if not phone:
        print("❌ Cannot trigger VAPI call: no phone number")
        return {"success": False, "error": "No phone number"}

    payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": phone,
            "name": customer_name or "there"
        },
        "assistantOverrides": {
            "variableValues": {
                "customer_name": customer_name or "there",
                "conversation_summary": summary or "Interested in AI solutions.",
                "product_interest": product_interest or "AI solutions",
                "interest_level": interest_level
            }
        }
    }

    try:
        resp = requests.post(
            "https://api.vapi.ai/call/phone",
            headers={
                "Authorization": f"Bearer {VAPI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )

        data = resp.json()

        if resp.status_code in [200, 201]:
            call_id = data.get("id", "unknown")
            print(f"📞 VAPI call triggered! Call ID: {call_id}, To: {phone}")
            return {"success": True, "call_id": call_id, "status": data.get("status")}
        else:
            error_msg = data.get("message", str(data))
            print(f"❌ VAPI call failed: {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        print(f"❌ VAPI call exception: {e}")
        return {"success": False, "error": str(e)}
