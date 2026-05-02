"""
Configuration module for Multi-Domain Support Triage Agent.

All constants, model names, paths, and thresholds are centralized here.
No configuration values should be hardcoded in other modules.
"""

import os

# ============================================================================
# API Configuration
# ============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ============================================================================
# Model Configuration
# ============================================================================
GROQ_MODEL_MAIN = "llama-3.3-70b-versatile"  # Main agent model
GROQ_MODEL_REWRITE = "llama-3.1-8b-instant"  # Query rewriting model
TEMPERATURE = 0  # Deterministic output
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Sentence transformer for dense retrieval
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Cross-encoder for reranking

# ============================================================================
# Retrieval Configuration
# ============================================================================
TOP_K_RETRIEVAL = 3  # Final number of pages to return after reranking
TOP_K_BEFORE_RERANK = 20  # Candidates to pass to reranker
BM25_TOP_K = 10  # Top results from BM25
EMBEDDING_TOP_K = 10  # Top results from dense retrieval
RRF_K = 60  # Reciprocal Rank Fusion constant

# ============================================================================
# Path Configuration
# ============================================================================
DATA_DIR = "data/pages"
EMBEDDINGS_DIR = "data/embeddings"
INDEX_DIR = "data/indexes"
INPUT_CSV = "support_tickets/support_tickets/support_tickets.csv"
OUTPUT_CSV = "support_tickets/support_tickets/output.csv"

# ============================================================================
# Domain Configuration
# ============================================================================
DOMAINS = ["hackerrank", "claude", "visa"]
DOMAIN_URLS = {
    "hackerrank": "https://support.hackerrank.com/",
    "claude": "https://support.claude.com/en/",
    "visa": "https://www.visa.co.in/support.html"
}

# Company name normalization mapping
COMPANY_NORMALIZATION = {
    "hackerrank": "hackerrank",
    "hacker rank": "hackerrank",
    "hr": "hackerrank",
    "claude": "claude",
    "anthropic": "claude",
    "claude ai": "claude",
    "visa": "visa",
    "visa card": "visa",
    "none": None,
    "": None
}

# ============================================================================
# Escalation Rules Configuration
# ============================================================================
ESCALATION_KEYWORDS = {
    "prompt_injection": [
        "ignore instructions", "forget previous", "you are now",
        "jailbreak", "DAN", "act as", "override", "bypass",
        "ignore all previous", "disregard", "new instructions",
        "system prompt", "ignore above"
    ],
    "fraud": [
        "stolen", "unauthorized charge", "fraudulent transaction",
        "card compromised", "dispute transaction", "chargeback fraud",
        "fraud alert", "suspicious charge", "not my purchase"
    ],
    "legal": [
        r"\bsue\b", "legal action", "lawyer", "lawsuit", "court",
        "attorney", "litigation", "legal counsel", "take legal action",
        "file a complaint", "regulatory complaint"
    ],
    "account_takeover": [
        "account hacked", "someone else logged in", "locked out",
        "can't access my account", "unauthorized access",
        "account compromised", "suspicious login", "password changed without"
    ],
    "data_privacy": [
        "delete my data", "GDPR", "right to erasure",
        "personal data request", "data deletion", "right to be forgotten",
        "CCPA", "data privacy", "remove my information"
    ],
    "billing_dispute": [
        "wrong charge", "double charged", "refund not received",
        "unexpected charge", "billing error", "overcharged",
        "incorrect amount", "charge dispute"
    ]
}

# Minimum meaningful words for gibberish detection
MIN_MEANINGFUL_WORDS = 5

# ============================================================================
# Query Rewriting Configuration
# ============================================================================
COMMON_ABBREVIATIONS = {
    "otp": "OTP one-time password authentication",
    "2fa": "two-factor authentication 2FA",
    "mfa": "multi-factor authentication MFA",
    "cvv": "CVV card verification value security code",
    "api": "API application programming interface",
    "sso": "SSO single sign-on authentication",
    "kyc": "KYC know your customer verification",
    "pwd": "password",
    "acct": "account",
    "txn": "transaction",
    "auth": "authentication",
    "cc": "credit card",
    "db": "database"
}

MAX_REWRITE_WORDS = 30

# ============================================================================
# Multi-Request Detection Configuration
# ============================================================================
TOPIC_SHIFT_KEYWORDS = {
    "billing": ["charge", "payment", "refund", "invoice", "billing", "subscription"],
    "authentication": ["login", "password", "2fa", "otp", "access", "sign in"],
    "account": ["account", "profile", "settings", "delete", "close"],
    "technical": ["error", "bug", "not working", "broken", "issue", "problem"],
    "feature": ["feature", "request", "add", "new", "enhancement", "suggestion"]
}

# ============================================================================
# Miscellaneous Configuration
# ============================================================================
RANDOM_SEED = 42  # For reproducibility
MAX_CONTEXT_LENGTH = 4000  # Maximum characters of context to pass to LLM
SCRAPER_MAX_PAGES = 100  # Maximum pages to scrape per domain
SCRAPER_TIMEOUT = 10  # Timeout for HTTP requests in seconds
