"""
Output schema definition for support ticket triage.

Defines the Pydantic model for structured output validation.
Ensures all agent responses conform to the required format.
"""

from pydantic import BaseModel, Field
from typing import Literal


class TicketOutput(BaseModel):
    """
    Structured output schema for support ticket triage.
    
    Attributes:
        status: Whether the ticket was replied to or escalated to human agent
        product_area: Relevant support category/categories (use " | " separator for multiple)
        response: User-facing answer grounded in retrieved context only
        justification: Internal reasoning traceable to the corpus
        request_type: Classification of the request type
    """
    status: Literal["replied", "escalated"] = Field(
        description="Whether ticket was handled automatically or needs human escalation"
    )
    product_area: str = Field(
        description="Most relevant support category, e.g. 'Account Access' or 'Billing | Authentication'"
    )
    response: str = Field(
        description="User-facing answer based solely on retrieved documentation"
    )
    justification: str = Field(
        description="Internal reasoning explaining the response, traceable to corpus"
    )
    request_type: Literal["product_issue", "feature_request", "bug", "invalid"] = Field(
        description="Classification of the request type"
    )
