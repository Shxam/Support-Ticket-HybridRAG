"""
Main agent orchestration module.

Orchestrates the full pipeline for each ticket:
1. Escalation check (rule-based)
2. Query rewriting (Advanced RAG)
3. Hybrid retrieval (BM25 + embeddings + RRF)
4. Cross-encoder reranking (Advanced RAG)
5. LLM response generation with anti-hallucination prompt
"""

import json
from typing import Dict, Any
from groq import Groq
from config import (
    GROQ_API_KEY,
    GROQ_MODEL_MAIN,
    TEMPERATURE,
    MAX_CONTEXT_LENGTH
)
from output_schema import TicketOutput
from escalation import check_escalation, get_escalation_response
from query_rewriter import rewrite_query
from page_retriever import retrieve_pages
from reranker import rerank_documents
from utils import (
    combine_ticket_text,
    normalize_company,
    detect_multiple_requests,
    truncate_context,
    infer_company_from_content
)


def build_context_from_pages(pages: list[Dict]) -> str:
    """
    Build context string from retrieved pages.
    
    Args:
        pages: List of page dictionaries
        
    Returns:
        Formatted context string
    """
    context_parts = []
    
    for i, page in enumerate(pages, 1):
        context_parts.append(f"--- Document {i} ---")
        context_parts.append(page['text'])
        context_parts.append("")
    
    return "\n".join(context_parts)


def build_system_prompt(company: str, retrieved_context: str, ticket: str) -> str:
    """
    Build anti-hallucination system prompt.
    
    Args:
        company: Company name
        retrieved_context: Retrieved documentation context
        ticket: User ticket text
        
    Returns:
        Complete system prompt
    """
    schema_json = TicketOutput.model_json_schema()
    
    prompt = f"""You are a support triage agent for {company.title() if company else 'multi-domain support'}.

Your job is to answer the user's support ticket using ONLY the retrieved context provided below.

STRICT RULES:
1. Do NOT use any knowledge outside the provided context.
2. Do NOT invent policies, steps, or features not mentioned in the context.
3. If the context does not contain a clear answer, set status to "escalated" and response to: "I don't have sufficient information in our support documentation to answer this accurately. Escalating to a human agent."
4. If the ticket contains multiple requests, address each one separately in the response.
5. Keep response professional, concise, and user-facing.
6. Base your justification on specific information from the retrieved context.
7. Choose the most appropriate product_area based on the context.
8. Classify request_type as: "product_issue" (user needs help), "feature_request" (wants new feature), "bug" (something broken), or "invalid" (off-topic/unclear).

Retrieved Context:
{retrieved_context}

Ticket:
{ticket}

Respond ONLY with valid JSON matching this exact schema:
{json.dumps(schema_json, indent=2)}"""

    return prompt


def call_llm(system_prompt: str) -> Dict[str, Any]:
    """
    Call Groq LLM to generate structured response.
    
    Args:
        system_prompt: Complete system prompt with context and ticket
        
    Returns:
        Parsed JSON response as dictionary
    """
    client = Groq(api_key=GROQ_API_KEY)
    
    response = client.chat.completions.create(
        model=GROQ_MODEL_MAIN,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": "Please analyze this ticket and respond with the JSON output."
            }
        ],
        temperature=TEMPERATURE,
        response_format={"type": "json_object"}
    )
    
    # Parse JSON response
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    
    return response_json


def process_ticket(issue: str, subject: str, company: str) -> TicketOutput:
    """
    Process a single support ticket through the full pipeline.
    
    Pipeline:
    1. Combine and normalize input
    2. Check escalation rules (pre-LLM)
    3. Rewrite query (Advanced RAG)
    4. Hybrid retrieval (BM25 + embeddings + RRF)
    5. Cross-encoder reranking (Advanced RAG)
    6. LLM generation with anti-hallucination prompt
    
    Args:
        issue: Ticket issue text
        subject: Ticket subject line
        company: Company name (HackerRank, Claude, Visa, None)
        
    Returns:
        TicketOutput with structured response
    """
    # Combine ticket text
    ticket_text = combine_ticket_text(issue, subject)
    
    # Normalize company name
    normalized_company = normalize_company(company)
    
    # If company is None, try to infer from content
    if normalized_company is None:
        normalized_company = infer_company_from_content(ticket_text)
    
    # Check for multiple requests
    has_multiple, topics = detect_multiple_requests(ticket_text)
    
    # Step 1: Check escalation rules (pre-LLM)
    escalation_result = check_escalation(ticket_text)
    
    if escalation_result['triggered']:
        # Return escalated response immediately
        return TicketOutput(
            status=escalation_result['status'],
            product_area="Security & Compliance" if "fraud" in escalation_result['reason'] or "legal" in escalation_result['reason'] else "General Support",
            response=get_escalation_response(escalation_result['reason'], escalation_result['request_type']),
            justification=f"Rule-based escalation: {escalation_result['reason']}",
            request_type=escalation_result['request_type']
        )
    
    # Step 2: Query rewriting (Advanced RAG)
    rewritten_query = rewrite_query(ticket_text, normalized_company)
    
    # Step 3: Hybrid retrieval (BM25 + embeddings + RRF)
    retrieved_docs = retrieve_pages(rewritten_query, normalized_company)
    
    if not retrieved_docs:
        # No documents retrieved - escalate
        return TicketOutput(
            status="escalated",
            product_area="General Support",
            response="I don't have sufficient information in our support documentation to answer this accurately. Escalating to a human agent.",
            justification="No relevant documentation found during retrieval",
            request_type="product_issue"
        )
    
    # Step 4: Cross-encoder reranking (Advanced RAG)
    reranked_docs = rerank_documents(rewritten_query, retrieved_docs)
    
    # Step 5: Build context and call LLM
    context = build_context_from_pages(reranked_docs)
    context = truncate_context(context, MAX_CONTEXT_LENGTH)
    
    system_prompt = build_system_prompt(normalized_company or "support", context, ticket_text)
    
    try:
        response_json = call_llm(system_prompt)
        
        # Validate and return
        output = TicketOutput(**response_json)
        return output
    
    except Exception as e:
        # LLM call failed - escalate
        return TicketOutput(
            status="escalated",
            product_area="General Support",
            response="An error occurred while processing your request. Escalating to a human agent.",
            justification=f"LLM processing error: {str(e)}",
            request_type="product_issue"
        )
