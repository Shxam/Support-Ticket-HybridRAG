# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set API key**:
```bash
export GROQ_API_KEY=your_groq_api_key_here
```

## Run (3 steps)

### Step 1: Scrape Documentation
```bash
python code/scraper.py
```
⏱️ Takes 10-30 minutes. Crawls HackerRank, Claude, and Visa support pages.

### Step 2: Build Indexes
```bash
python code/page_index.py
```
⏱️ Takes 5-10 minutes. Builds BM25 + embedding indexes. Downloads models on first run (~170MB).

### Step 3: Process Tickets
```bash
python code/main.py
```
⏱️ Takes 1-2 minutes for 29 tickets. Processes tickets and generates `output.csv`.

## Output

Results saved to: `support_tickets/support_tickets/output.csv`

Columns:
- `issue`, `subject`, `company` (original input)
- `response` (user-facing answer)
- `product_area` (support category)
- `status` (replied/escalated)
- `request_type` (product_issue/feature_request/bug/invalid)
- `justification` (internal reasoning)

## Architecture

**Hybrid RAG + Advanced RAG**:
1. ⚡ Rule-based escalation (fraud, legal, prompt injection)
2. 🔄 Query rewriting (expand abbreviations, fix typos)
3. 🔍 Hybrid retrieval (BM25 + embeddings + RRF fusion)
4. 🎯 Cross-encoder reranking (top-3 most relevant)
5. 🤖 LLM generation (anti-hallucination prompt, temp=0)

## Troubleshooting

- **"Index not found"**: Run step 2 first
- **"No documents"**: Run step 1 first
- **"API key not set"**: Set `GROQ_API_KEY` environment variable
- **Slow first run**: Models are being downloaded (~170MB)

## Files Generated

```
data/
├── pages/          # Scraped documentation (step 1)
├── embeddings/     # Dense embeddings (step 2)
└── indexes/        # BM25 indexes (step 2)

support_tickets/support_tickets/
└── output.csv      # Final results (step 3)
```

## Key Features

✅ Handles multiple requests per ticket
✅ Infers company from content when company="None"
✅ Detects prompt injection, fraud, legal threats
✅ Removes PII automatically
✅ Zero hallucination (grounded in docs only)
✅ Deterministic output (temp=0)
✅ Graceful error handling (escalates on failure)

For detailed documentation, see `code/README.md`.
