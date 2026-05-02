"""
Utility functions for ticket processing.

Includes PII removal, company normalization, and multi-request detection.
"""

import re
from typing import List, Tuple, Optional
from config import COMPANY_NORMALIZATION, TOPIC_SHIFT_KEYWORDS


def remove_pii(text: str) -> str:
    """
    Remove personally identifiable information from text.
    
    Removes:
    - Email addresses
    - Phone numbers
    - Credit card numbers (partial)
    - Order IDs and transaction IDs
    - URLs with potential PII
    
    Args:
        text: Input text potentially containing PII
        
    Returns:
        Text with PII replaced by placeholders
    """
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Remove phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b', '[PHONE]', text)
    
    # Remove credit card numbers (partial, keep last 4 digits pattern)
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)
    
    # Remove order/transaction IDs (common patterns)
    text = re.sub(r'\b(order[_\s]?id|transaction[_\s]?id|txn[_\s]?id)[:\s]+[A-Za-z0-9_-]+\b', '[ORDER_ID]', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcs_live_[A-Za-z0-9]+\b', '[ORDER_ID]', text)
    
    # Remove URLs
    text = re.sub(r'https?://[^\s]+', '[URL]', text)
    
    return text


def normalize_company(company: str) -> Optional[str]:
    """
    Normalize company name to standard format.
    
    Args:
        company: Raw company name from CSV
        
    Returns:
        Normalized company name (lowercase) or None if invalid/unknown
    """
    if not company or not isinstance(company, str):
        return None
    
    company_lower = company.strip().lower()
    return COMPANY_NORMALIZATION.get(company_lower, company_lower if company_lower in ["hackerrank", "claude", "visa"] else None)


def detect_multiple_requests(ticket_text: str) -> Tuple[bool, List[str]]:
    """
    Detect if ticket contains multiple distinct requests.
    
    Uses keyword clustering to identify topic shifts within the ticket.
    
    Args:
        ticket_text: Combined issue and subject text
        
    Returns:
        Tuple of (has_multiple_requests, list_of_detected_topics)
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', ticket_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if len(sentences) < 2:
        return False, []
    
    # Detect topics in each sentence
    sentence_topics = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        detected_topics = []
        
        for topic, keywords in TOPIC_SHIFT_KEYWORDS.items():
            if any(keyword in sentence_lower for keyword in keywords):
                detected_topics.append(topic)
        
        sentence_topics.append(detected_topics)
    
    # Find unique topics across all sentences
    all_topics = set()
    for topics in sentence_topics:
        all_topics.update(topics)
    
    # Multiple requests if we have 2+ distinct topics
    has_multiple = len(all_topics) >= 2
    
    return has_multiple, list(all_topics)


def combine_ticket_text(issue: str, subject: str) -> str:
    """
    Combine issue and subject into single text for processing.
    
    Args:
        issue: Main ticket body
        subject: Ticket subject line (may be empty or noisy)
        
    Returns:
        Combined text with subject prepended if meaningful
    """
    issue = str(issue).strip() if issue else ""
    subject = str(subject).strip() if subject else ""
    
    # Only include subject if it's meaningful and not redundant
    if subject and len(subject) > 3 and subject.lower() not in issue.lower():
        return f"{subject}. {issue}"
    
    return issue


def merge_status(status1: str, status2: str) -> str:
    """
    Merge two status values, preferring escalated over replied.
    
    Args:
        status1: First status value
        status2: Second status value
        
    Returns:
        Merged status (escalated takes precedence)
    """
    if status1 == "escalated" or status2 == "escalated":
        return "escalated"
    return "replied"


def merge_request_types(types: List[str]) -> str:
    """
    Merge multiple request types into pipe-separated string.
    
    Args:
        types: List of request type strings
        
    Returns:
        Pipe-separated unique request types
    """
    unique_types = []
    for t in types:
        if t and t not in unique_types:
            unique_types.append(t)
    
    return " | ".join(unique_types) if unique_types else "product_issue"


def merge_product_areas(areas: List[str]) -> str:
    """
    Merge multiple product areas into pipe-separated string.
    
    Args:
        areas: List of product area strings
        
    Returns:
        Pipe-separated unique product areas
    """
    unique_areas = []
    for area in areas:
        if area and area not in unique_areas:
            unique_areas.append(area)
    
    return " | ".join(unique_areas) if unique_areas else "General Support"


def clean_text(text: str) -> str:
    """
    Clean text by removing excessive whitespace and special characters.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def truncate_context(context: str, max_length: int) -> str:
    """
    Truncate context to maximum length while preserving complete sentences.
    
    Args:
        context: Full context text
        max_length: Maximum character length
        
    Returns:
        Truncated context
    """
    if len(context) <= max_length:
        return context
    
    # Truncate and try to end at sentence boundary
    truncated = context[:max_length]
    last_period = truncated.rfind('.')
    
    if last_period > max_length * 0.8:  # If we can keep 80%+ of content
        return truncated[:last_period + 1]
    
    return truncated + "..."


def infer_company_from_content(ticket_text: str) -> Optional[str]:
    """
    Attempt to infer company from ticket content when company field is None.
    
    Args:
        ticket_text: Combined ticket text
        
    Returns:
        Inferred company name or None
    """
    text_lower = ticket_text.lower()
    
    # HackerRank indicators
    hackerrank_keywords = [
        "hackerrank", "hacker rank", "coding test", "assessment",
        "mock interview", "recruiter", "test score", "coding challenge"
    ]
    if any(keyword in text_lower for keyword in hackerrank_keywords):
        return "hackerrank"
    
    # Claude indicators
    claude_keywords = [
        "claude", "anthropic", "workspace", "team workspace",
        "ai model", "chatbot", "conversation"
    ]
    if any(keyword in text_lower for keyword in claude_keywords):
        return "claude"
    
    # Visa indicators
    visa_keywords = [
        "visa card", "visa", "credit card", "debit card",
        "merchant", "card payment", "cvv"
    ]
    if any(keyword in text_lower for keyword in visa_keywords):
        return "visa"
    
    return None
