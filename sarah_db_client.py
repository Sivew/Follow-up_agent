import os
import requests
import urllib.parse
from typing import Optional, Dict, Any

class SarahDBClient:
    """
    Client for the Lead Conversation Management System API.
    Base URL: https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
    """
    
    BASE_URL = "https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key is required")
        self.api_key = api_key
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_customer(self, 
                       email: Optional[str] = None, 
                       phone: Optional[str] = None, 
                       name: Optional[str] = None,
                       phone_normalized: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new customer.
        At least one of email or phone is required.
        """
        if not email and not phone:
            raise ValueError("At least one of 'email' or 'phone' is required to create a customer")
            
        payload = {}
        if email: payload["email"] = email
        if phone: payload["phone"] = phone
        if name: payload["name"] = name
        if phone_normalized: payload["phone_normalized"] = phone_normalized
        
        url = f"{self.BASE_URL}/customers"
        
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create customer: {str(e)}")

    def list_customers(self, limit: int = 100, offset: int = 0) -> dict:
        """List all customers."""
        url = f"{self.BASE_URL}/customers?limit={limit}&offset={offset}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list customers: {str(e)}")

    def get_context(self, identifier: str, lookup_by: str = "id") -> Dict[str, Any]:
        """
        Get customer context by ID, email, or phone.
        identifier: The value to look up (e.g., "john@example.com", "+1555...")
        lookup_by: "id", "email", "phone", or "phone_normalized" (default "id")
        """
        valid_types = ["id", "email", "phone", "phone_normalized"]
        if lookup_by not in valid_types:
            raise ValueError(f"Invalid lookup_by '{lookup_by}'. Must be one of {valid_types}")

        # URL encode the identifier (critical for emails/phones with +)
        encoded_id = urllib.parse.quote(identifier, safe='')
        
        url = f"{self.BASE_URL}/context/{encoded_id}?by={lookup_by}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            # Handle 404 gracefully? Or let caller handle?
            # For now, re-raise with context
            raise Exception(f"Failed to get context for {identifier}: {str(e)}")

    def log_message(self, 
                    customer_id: int, 
                    channel: str, 
                    identifier: str, 
                    direction: str, 
                    body: str, 
                    context_id: Optional[str] = None,
                    subject: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Log an inbound or outbound message.
        Returns: Dict containing 'log_id' and 'context_id'
        """
        payload = {
            "customer_id": customer_id,
            "channel": channel,
            "channel_identifier": identifier,
            "direction": direction,
            "message_body": body
        }
        
        if context_id:
            payload["context_id"] = context_id
        if subject:
            payload["message_subject"] = subject
        if metadata:
            payload["metadata"] = metadata

        url = f"{self.BASE_URL}/log"
        
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to log message: {str(e)}")

    def update_conversation(self, 
                            context_id: str, 
                            summary: Optional[str] = None,
                            intent: Optional[str] = None, 
                            sentiment: Optional[str] = None,
                            last_agent_action: Optional[str] = None,
                            open_questions: Optional[str] = None) -> Dict[str, Any]:
        """
        Update conversation state after AI processing.
        Only provide fields you want to update.
        """
        if not context_id:
             raise ValueError("Context ID is required for update")

        payload = {}
        if summary: payload["summary"] = summary
        if intent: payload["intent"] = intent
        if sentiment: payload["sentiment"] = sentiment
        if last_agent_action: payload["last_agent_action"] = last_agent_action
        if open_questions: payload["open_questions"] = open_questions

        if not payload:
            return {"status": "no_changes"}

        url = f"{self.BASE_URL}/context/{context_id}/update"
        
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to update conversation {context_id}: {str(e)}")
