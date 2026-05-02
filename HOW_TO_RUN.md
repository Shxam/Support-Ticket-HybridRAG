# How to Run the Multi-Domain Support Triage Agent

## Quick Start (3 Steps)

### Prerequisites
- Python 3.8 or higher
- Groq API key (get one at https://console.groq.com/)

---

## Step 1: Install Dependencies

Open PowerShell/Terminal in the project directory and run:

```powershell
pip install -r requirements.txt
```

This installs all required packages (~5 minutes on first run).

---

## Step 2: Set Your API Key

**On Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

**On Mac/Linux (Bash):**
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

**To make it permanent (optional):**
- Windows: Add to System Environment Variables
- Mac/Linux: Add to `~/.bashrc` or `~/.zshrc`

---

## Step 3: Run the Pipeline

### Option A: Use Existing Data (Fastest - Already Done!)

The system has already been run with sample documentation. Just process tickets:

```powershell
$env:GROQ_API_KEY="your_key_here"
python code/main.py
```

**Output:** `support_tickets/support_tickets/output.csv`

---

### Option B: Full Pipeline from Scratch

If you want to scrape fresh documentation and rebuild indexes:

#### 3a. Scrape Support Documentation (10-30 minutes)
```powershell
$env:GROQ_API_KEY="your_key_here"
python code/scraper.py
```

This crawls:
- HackerRank support pages
- Claude support pages  
- Visa support pages

Saves to: `data/pages/{domain}/`

#### 3b. Build Indexes (5-10 minutes)
```powershell
$env:GROQ_API_KEY="your_key_here"
python code/page_index.py
```

This creates:
- BM25 sparse indexes
- Dense embedding indexes
- Global index for company="None"

**Note:** First run downloads models (~170MB)

#### 3c. Process Tickets (1-2 minutes)
```powershell
$env:GROQ_API_KEY="your_key_here"
python code/main.py
```

Processes all tickets in `support_tickets/support_tickets/support_tickets.csv`

---

## Complete Command Sequence

**Copy and paste this (replace YOUR_KEY):**

```powershell
# Set API key
$env:GROQ_API_KEY="YOUR_GROQ_API_KEY_HERE"

# Option 1: Just process tickets (uses existing data)
python code/main.py

# Option 2: Full pipeline from scratch
# python code/scraper.py      # 10-30 min
# python code/page_index.py   # 5-10 min
# python code/main.py         # 1-2 min
```

---

## What You'll See

### During Processing:
```
================================================================================
MULTI-DOMAIN SUPPORT TRIAGE AGENT
================================================================================
Reading tickets from: support_tickets/support_tickets/support_tickets.csv
Loaded 29 tickets

Processing tickets: 100%|████████████████| 29/29 [01:45<00:00,  3.62s/it]

[TICKET 01/29] replied   — domain: Claude       — type: product_issue
[TICKET 02/29] replied   — domain: HackerRank   — type: invalid
[TICKET 03/29] replied   — domain: Visa         — type: product_issue
...
[TICKET 29/29] replied   — domain: Visa         — type: product_issue

Writing results to: support_tickets/support_tickets/output.csv

================================================================================
PROCESSING COMPLETE
================================================================================
Total tickets processed: 29
Replied: 24
Escalated: 5

Output saved to: support_tickets/support_tickets/output.csv
================================================================================
```

---

## Output File

**Location:** `support_tickets/support_tickets/output.csv`

**Columns:**
- `issue` - Original ticket text
- `subject` - Original subject
- `company` - Original company field
- `response` - User-facing answer
- `product_area` - Support category
- `status` - "replied" or "escalated"
- `request_type` - Classification
- `justification` - Internal reasoning

---

## Troubleshooting

### Error: "GROQ_API_KEY not set"
**Solution:** Set the environment variable:
```powershell
$env:GROQ_API_KEY="your_key_here"
```

### Error: "Index not found"
**Solution:** Run the indexing step first:
```powershell
python code/page_index.py
```

### Error: "No documents found"
**Solution:** Either:
1. Use the existing sample data in `data/pages/` (already created)
2. Or run the scraper: `python code/scraper.py`

### Error: "Module not found"
**Solution:** Install dependencies:
```powershell
pip install -r requirements.txt
```

### Slow First Run
**Reason:** Downloading models (~170MB)
- `all-MiniLM-L6-v2` (~80MB)
- `cross-encoder/ms-marco-MiniLM-L-6-v2` (~90MB)

Subsequent runs use cached models and are much faster.

---

## Testing with Your Own Tickets

1. Edit `support_tickets/support_tickets/support_tickets.csv`
2. Add your tickets with columns: `Issue`, `Subject`, `Company`
3. Run: `python code/main.py`
4. Check output in `support_tickets/support_tickets/output.csv`

**Example CSV format:**
```csv
Issue,Subject,Company
"My account is locked",Account Access,HackerRank
"How do I reset my password?",Password Reset,Claude
"Dispute a charge",Billing Issue,Visa
```

---

## Configuration

Edit `code/config.py` to customize:
- Models (LLM, embeddings, reranker)
- Retrieval parameters (top-k, RRF constant)
- File paths
- Escalation keywords
- Abbreviation expansions

---

## Performance

**Typical Processing Time:**
- Escalation check: <1ms
- Query rewriting: ~200-500ms
- Retrieval: ~50-100ms
- Reranking: ~100-200ms
- LLM generation: ~1-3s

**Total per ticket:** ~2-4 seconds

**For 29 tickets:** ~1-2 minutes

---

## System Requirements

- **Python:** 3.8+
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 500MB for models and data
- **Internet:** Required for API calls and model downloads

---

## Need Help?

1. Check `code/README.md` for detailed documentation
2. Review `EXECUTION_SUMMARY.md` for example results
3. Check error messages - they're descriptive
4. Ensure API key is valid and has credits

---

## Already Processed?

The system has already been run successfully! Check:
- **Output:** `support_tickets/support_tickets/output.csv` (29 tickets processed)
- **Summary:** `EXECUTION_SUMMARY.md` (detailed results)

To process again with different tickets, just edit the input CSV and run `python code/main.py`.
