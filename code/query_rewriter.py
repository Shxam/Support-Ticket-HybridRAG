"""
Query rewriting module for Advanced RAG.

Rewrites noisy support tickets into clean search queries before retrieval.
Expands abbreviations, fixes typos, removes PII and emotional content.
"""

import re
from groq import Groq
from config import (
    GROQ_API_KEY,
    GROQ_MODEL_REWRITE,
    TEMPERATURE,
    COMMON_ABBREVIATIONS,
    MAX_REWRITE_WORDS
)
from utils import remove_pii


def expand_abbreviations(text: str) -> str:
    """
    Expand common abbreviations in text.
    
    Args:
        text: Input text with potential abbreviations
        
    Returns:
        Text with abbreviations expanded
    """
    text_lower = text.lower()
    
    for abbr, expansion in COMMON_ABBREVIATIONS.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(abbr) + r'\b'
        text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
    
    return text


def rewrite_query(ticket_text: str, company: str = None) -> str:
    """
    Rewrite support ticket into clean search query using LLM.
    
    This is the pre-retrieval query rewriting step of Advanced RAG.
    
    Process:
    1. Remove PII
    2. Expand abbreviations
    3. Use LLM to clean, fix typos, remove emotional content
    4. Add domain context if company is known
    5. Keep output under MAX_REWRITE_WORDS
    
    Args:
        ticket_text: Raw ticket text
        company: Company name if known (hackerrank, claude, visa, or None)
        
    Returns:
        Rewritten clean search query
    """
    # Remove PII first
    cleaned_text = remove_pii(ticket_text)
    
    # Expand abbreviations
    expanded_text = expand_abbreviations(cleaned_text)
    
    # Build prompt for query rewriting
    domain_context = ""
    if company:
        domain_context = f" for {company.title()}"
    
    prompt = f"""Rewrite this support ticket into a clean search query{domain_context}.

Rules:
1. Remove emotional language, profanity, and filler words
2. Fix obvious typos and grammar
3. Keep technical terms and product names
4. Focus on the core issue or question
5. Output must be under {MAX_REWRITE_WORDS} words
6. Do not add information not in the original ticket
7. If multiple issues, include all key points

Original ticket:
{expanded_text}

Rewritten search query:"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        response = client.chat.completions.create(
            model=GROQ_MODEL_REWRITE,
            messages=[
                {
                    "role": "system",
                    "content": "You are a query rewriting assistant. Rewrite support tickets into clean, focused search queries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=TEMPERATURE,
            max_tokens=100
        )
        
        rewritten = response.choices[0].message.content.strip()
        
        # Ensure it's not too long
        words = rewritten.split()
        if len(words) > MAX_REWRITE_WORDS:
            rewritten = " ".join(words[:MAX_REWRITE_WORDS])
        
        return rewritten
    
    except Exception as e:
        # Fallback: return cleaned and expanded text if LLM fails
        print(f"Warning: Query rewriting failed ({str(e)}), using fallback")
        words = expanded_text.split()
        if len(words) > MAX_REWRITE_WORDS:
            return " ".join(words[:MAX_REWRITE_WORDS])
        return expanded_text
