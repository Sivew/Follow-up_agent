import logging
import os

def log_event(message):
    """
    Logs events to stdout and optionally to a file or external service.
    """
    logging.info(message)
    # TODO: Add external logging (Sentry, Datadog, etc.) if needed

def is_human_handoff_needed(message_body):
    """
    Detects if a human agent should take over the conversation.
    Returns True if keywords are found.
    """
    handoff_keywords = [
        "call me",
        "speak to a human",
        "real person",
        "representative",
        "agent",
        "help",
        "support",
        "emergency",
        "urgent"
    ]
    
    body_lower = message_body.lower()
    for keyword in handoff_keywords:
        if keyword in body_lower:
            return True
            
    return False
