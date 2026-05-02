# Multi-Domain Support Triage Agent

A production-ready terminal-based support triage system that processes support tickets across three domains (HackerRank, Claude, Visa) using **Hybrid RAG enhanced with Advanced RAG techniques**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SUPPORT TICKET INPUT                         │
│                      (issue, subject, company)                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ESCALATION CHECK (escalation.py)                  │
│              Rule-based: fraud, legal, prompt injection              │
│                         NO LLM - Pure Rules                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Escalated?             │
                    └────────────┬────────────┘
                                 │ No
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              QUERY REWRITING (query_rewriter.py)                     │
│                    Advanced RAG: Pre-Retrieval                       │
│   • Expand abbreviations (OTP, 2FA, CVV)                            │
│   • Fix typos, remove PII                                           │
│   • Clean emotional content                                         │
│   • LLM: llama-3.1-8b-instant, temp=0                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│            HYBRID RETRIEVAL (page_retriever.py)                      │
│                      Hybrid RAG: Dual Retrieval                      │
│                                                                      │
│   ┌──────────────────┐              ┌──────────────────┐           │
│   │  BM25 Sparse     │              │  Dense Embedding │           │
│   │  Retrieval       │              │  Retrieval       │           │
│   │  (exact terms)   │              │  (semantic)      │           │
│   │  Top-10          │              │  Top-10          │           │
│   └────────┬─────────┘              └────────┬─────────┘           │
│            │                                  │                     │
│            └──────────────┬───────────────────┘                     │
│                           ▼                                         │
│              ┌────────────────────────┐                             │
│              │ Reciprocal Rank Fusion │                             │
│              │  score = Σ 1/(k+rank)  │                             │
│              │       k = 60           │                             │
│              └────────────┬───────────┘                             │
│                           │                                         │
│                           ▼                                         │
│                      Top-20 Candidates                              │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              CROSS-ENCODER RERANKING (reranker.py)                   │
│                   Advanced RAG: Post-Retrieval                       │
│   • Model: cross-encoder/ms-marco-MiniLM-L-6-v2                     │
│   • Scores each candidate against query                             │
│   • Returns top-3 most relevant pages                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LLM GENERATION (agent.py)                           │
│              Anti-Hallucination System Prompt                        │
│   • Model: llama-3.3-70b-versatile, temp=0                          │
│   • Grounded ONLY in retrieved context                              │
│   • Structured JSON output (Pydantic validation)                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         OUTPUT (output.csv)                          │
│   status, product_area, response, justification, request_type       │
└─────────────────────────────────────────────────────────────────────┘
```

## RAG Architecture Type

This system implements **Hybrid RAG (BM25 + dense embeddings with RRF fusion) enhanced with Advanced RAG techniques: query rewriting pre-retrieval and cross-encoder reranking post-retrieval.**

### Why This Architecture?

1. **Hybrid RAG (BM25 + Dense Embeddings)**:
   - **BM25 sparse retrieval**: Catches exact keyword matches (e.g., "CVV", "2FA", "chargeback")
   - **Dense embedding retrieval**: Handles semantic similarity and vague phrasing
   - **RRF fusion**: Combines both approaches to leverage their complementary strengths

2. **Advanced RAG - Pre-Retrieval (Query Rewriting)**:
   - Transforms noisy user tickets into clean search queries
   - Expands abbreviations and fixes typos
   - Removes PII and emotional content
   - Improves retrieval quality by clarifying intent

3. **Advanced RAG - Post-Retrieval (Cross-Encoder Reranking)**:
   - Reranks top candidates using cross-encoder
   - More accurate than bi-encoder similarity
   - Selects truly relevant pages, not just keyword matches

4. **Anti-Hallucination**:
   - Strict system prompt enforcing context-only responses
   - Temperature=0 for deterministic output
   - Structured output validation with Pydantic

## Project Structure

```
code/
├── main.py            # Entry point: reads CSV, loops tickets, writes output
├── config.py          # ALL constants (models, paths, thresholds)
├── agent.py           # Orchestrates full pipeline per ticket
├── escalation.py      # Pre-LLM rule-based safety layer
├── query_rewriter.py  # Advanced RAG: query rewriting pre-retrieval
├── utils.py           # PII removal, company normalization, multi-request detection
├── output_schema.py   # Pydantic schema for structured output validation
├── scraper.py         # Crawls and saves support pages from all 3 domains
├── page_index.py      # Builds BM25 + embedding indexes per domain + global
├── page_retriever.py  # Hybrid retrieval: BM25 + semantic + RRF fusion
├── reranker.py        # Cross-encoder reranking of top candidates
└── README.md          # This file

data/
├── pages/             # Scraped support pages (created by scraper.py)
│   ├── hackerrank/
│   ├── claude/
│   └── visa/
├── embeddings/        # Dense embeddings (created by page_index.py)
└── indexes/           # BM25 indexes and metadata (created by page_index.py)

support_tickets/
├── support_tickets.csv  # Input file
└── output.csv           # Output file (generated)
```

## Setup

### Prerequisites

- Python 3.8+
- Groq API key

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variable:

```bash
export GROQ_API_KEY=your_key_here
```

On Windows (PowerShell):
```powershell
$env:GROQ_API_KEY="your_key_here"
```

## Usage

### Step 1: Scrape Support Documentation

```bash
python code/scraper.py
```

This crawls support pages from HackerRank, Claude, and Visa domains and saves them to `data/pages/`.

**Note**: Scraping may take 10-30 minutes depending on the number of pages.

### Step 2: Build Indexes

```bash
python code/page_index.py
```

This builds:
- BM25 sparse indexes (per domain + global)
- Dense embedding indexes using sentence-transformers
- Metadata for document retrieval

**Note**: First run will download the embedding model (~80MB) and reranker model (~90MB).

### Step 3: Process Tickets

```bash
python code/main.py
```

This:
- Reads `support_tickets/support_tickets/support_tickets.csv`
- Processes each ticket through the full pipeline
- Writes structured output to `support_tickets/support_tickets/output.csv`

## Input Schema

CSV with columns:
- `Issue`: Main ticket body
- `Subject`: Subject line (may be blank or noisy)
- `Company`: "HackerRank", "Claude", "Visa", or "None"

## Output Schema

CSV with columns:
- `issue`: Original issue text
- `subject`: Original subject text
- `company`: Original company field
- `response`: User-facing answer grounded in documentation
- `product_area`: Relevant support category (e.g., "Account Access | Billing")
- `status`: "replied" or "escalated"
- `request_type`: "product_issue", "feature_request", "bug", or "invalid"
- `justification`: Internal reasoning traceable to corpus

## Configuration

All configuration is centralized in `code/config.py`:

- **Models**:
  - Main LLM: `llama-3.3-70b-versatile`
  - Query rewriting: `llama-3.1-8b-instant`
  - Embeddings: `all-MiniLM-L6-v2`
  - Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`

- **Retrieval**:
  - BM25 top-k: 10
  - Embedding top-k: 10
  - RRF constant: 60
  - Final top-k after reranking: 3

- **Paths**: All file paths configurable

## Escalation Rules

Pre-LLM rule-based escalation (no LLM calls) for:

1. **Prompt injection**: "ignore instructions", "jailbreak", "DAN", etc.
2. **Fraud signals**: "stolen", "unauthorized charge", "fraudulent transaction"
3. **Legal threats**: "sue", "lawsuit", "attorney", "litigation"
4. **Account takeover**: "account hacked", "locked out", "unauthorized access"
5. **Data privacy**: "delete my data", "GDPR", "right to erasure"
6. **Billing disputes**: "wrong charge", "double charged", "refund not received"
7. **Gibberish**: Fewer than 5 meaningful words
8. **Off-topic**: No support-related keywords

## Multi-Request Handling

The system detects tickets with multiple distinct requests:
- Answers ALL requests in the response field
- Uses highest-risk status across all requests
- Lists all product areas as "Area1 | Area2"
- Lists all request types as "type1 | type2"

## Known Limitations

1. **Scraping Limitations**:
   - May not capture all pages due to dynamic content or authentication
   - Some sites may block automated scraping
   - JavaScript-heavy pages may not render properly

2. **Retrieval Limitations**:
   - Quality depends on scraped documentation completeness
   - May miss relevant pages if query rewriting fails
   - Cross-domain queries (company="None") may be less accurate

3. **LLM Limitations**:
   - May still hallucinate despite strict prompting
   - Temperature=0 doesn't guarantee identical outputs
   - JSON parsing may fail on malformed responses

4. **Language Support**:
   - Optimized for English tickets
   - Non-English tickets may have degraded performance

5. **Edge Cases**:
   - Very long tickets may be truncated
   - Tickets with extreme typos may not rewrite well
   - Ambiguous requests may be misclassified

## Failure Modes

1. **No documents retrieved**: Ticket escalated with justification
2. **LLM call fails**: Ticket escalated with error message
3. **JSON parsing fails**: Ticket escalated with error message
4. **Index not found**: Error message, run `page_index.py` first
5. **API key missing**: Error message, set `GROQ_API_KEY`

## Environment Variables

Required:
- `GROQ_API_KEY`: Your Groq API key

## Performance

Typical processing time per ticket:
- Escalation check: <1ms
- Query rewriting: ~200-500ms
- Hybrid retrieval: ~50-100ms
- Reranking: ~100-200ms
- LLM generation: ~1-3s

**Total**: ~2-4 seconds per ticket

For 29 tickets: ~1-2 minutes total

## Troubleshooting

### "Index not found" error
Run `python code/page_index.py` to build indexes first.

### "No documents found" during indexing
Run `python code/scraper.py` to scrape documentation first.

### "GROQ_API_KEY not set" error
Set the environment variable: `export GROQ_API_KEY=your_key_here`

### Slow processing
- First run downloads models (~170MB total)
- Subsequent runs use cached models
- Consider reducing `SCRAPER_MAX_PAGES` in config.py for faster scraping

### Poor retrieval quality
- Increase `TOP_K_BEFORE_RERANK` in config.py
- Adjust `RRF_K` constant (higher = more weight to top ranks)
- Re-scrape with more pages per domain

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions, please refer to the code comments and docstrings.
