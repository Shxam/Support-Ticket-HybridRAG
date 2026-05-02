"""
Pre-LLM rule-based escalation layer.

Pure keyword and regex matching to detect high-risk tickets that require
immediate escalation without LLM processing. No AI/LLM calls in this module.
"""

import re
from typing import Dict, Any
from config import ESCALATION_KEYWORDS, MIN_MEANINGFUL_WORDS


def check_escalation(ticket_text: str) -> Dict[str, Any]:
    """
    Check if ticket should be escalated based on rule-based patterns.
    
    This function runs BEFORE any LLM processing to catch high-risk scenarios:
    - Prompt injection attempts
    - Fraud signals
    - Legal threats
    - Account takeover indicators
    - Data privacy requests
    - Billing disputes
    - Off-topic/gibberish content
    
    Args:
        ticket_text: Combined issue and subject text from ticket
        
    Returns:
        Dictionary with:
            - triggered: bool indicating if escalation rule matched
            - reason: str explaining which rule triggered
            - status: "escalated" or "replied"
            - request_type: classification of the request
    """
    ticket_lower = ticket_text.lower()
    
    # Check for prompt injection attempts
    for keyword in ESCALATION_KEYWORDS["prompt_injection"]:
        if keyword.lower() in ticket_lower:
            return {
                "triggered": True,
                "reason": f"prompt_injection: '{keyword}'",
                "status": "escalated",
                "request_type": "invalid"
            }
    
    # Check for fraud signals
    for keyword in ESCALATION_KEYWORDS["fraud"]:
        if keyword.lower() in ticket_lower:
            return {
                "triggered": True,
                "reason": f"fraud_signal: '{keyword}'",
                "status": "escalated",
                "request_type": "product_issue"
            }
    
    # Check for legal threats (using regex for word boundaries)
    for pattern in ESCALATION_KEYWORDS["legal"]:
        if re.search(pattern, ticket_lower, re.IGNORECASE):
            return {
                "triggered": True,
                "reason": f"legal_threat: '{pattern}'",
                "status": "escalated",
                "request_type": "product_issue"
            }
    
    # Check for account takeover indicators
    for keyword in ESCALATION_KEYWORDS["account_takeover"]:
        if keyword.lower() in ticket_lower:
            return {
                "triggered": True,
                "reason": f"account_takeover: '{keyword}'",
                "status": "escalated",
                "request_type": "product_issue"
            }
    
    # Check for data privacy requests
    for keyword in ESCALATION_KEYWORDS["data_privacy"]:
        if keyword.lower() in ticket_lower:
            return {
                "triggered": True,
                "reason": f"data_privacy: '{keyword}'",
                "status": "escalated",
                "request_type": "product_issue"
            }
    
    # Check for billing disputes
    for keyword in ESCALATION_KEYWORDS["billing_dispute"]:
        if keyword.lower() in ticket_lower:
            return {
                "triggered": True,
                "reason": f"billing_dispute: '{keyword}'",
                "status": "escalated",
                "request_type": "product_issue"
            }
    
    # Check for gibberish (too few meaningful words)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', ticket_text)
    if len(words) < MIN_MEANINGFUL_WORDS:
        return {
            "triggered": True,
            "reason": f"gibberish: only {len(words)} meaningful words",
            "status": "replied",
            "request_type": "invalid"
        }
    
    # Check if completely off-topic (no support-related keywords)
    support_keywords = [
        "help", "issue", "problem", "error", "not working", "broken",
        "account", "login", "password", "payment", "charge", "refund",
        "access", "support", "question", "how", "why", "what", "when",
        "can't", "cannot", "unable", "failed", "failure", "bug"
    ]
    
    has_support_keyword = any(keyword in ticket_lower for keyword in support_keywords)
    
    if not has_support_keyword and len(words) >= MIN_MEANINGFUL_WORDS:
        return {
            "triggered": True,
            "reason": "off_topic: no support-related keywords found",
            "status": "replied",
            "request_type": "invalid"
        }
    
    # No escalation triggered
    return {
        "triggered": False,
        "reason": "",
        "status": "",
        "request_type": ""
    }


def get_escalation_response(reason: str, request_type: str) -> str:
    """
    Generate appropriate response for escalated tickets.
    
    Args:
        reason: The escalation reason from check_escalation
        request_type: The request type classification
        
    Returns:
        User-facing response string
    """
    if "prompt_injection" in reason:
        return "Your request contains content that cannot be processed automatically. Please rephrase your question and resubmit."
    
    elif "fraud_signal" in reason or "billing_dispute" in reason:
        return "This matter requires immediate attention from our specialized team. Your case has been escalated to a human agent who will contact you within 24 hours."
    
    elif "legal_threat" in reason:
        return "Your inquiry involves legal matters that require review by our legal and customer relations team. A specialist will contact you within 48 hours."
    
    elif "account_takeover" in reason:
        return "For your security, this account access issue has been escalated to our security team. They will verify your identity and assist you within 24 hours."
    
    elif "data_privacy" in reason:
        return "Your data privacy request has been received and escalated to our privacy compliance team. They will process your request according to applicable regulations within the required timeframe."
    
    elif "gibberish" in reason:
        return "We couldn't understand your request. Please provide more details about the issue you're experiencing so we can assist you."
    
    elif "off_topic" in reason:
        return "Your message doesn't appear to be related to our support services. If you have a specific support question, please provide more details."
    
    else:
        return "Your request has been escalated to a human agent for review."
