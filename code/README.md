# Multi-Domain Support Triage Agent

A rule-based support ticket triage agent that routes and responds to support requests across three domains: **HackerRank**, **Claude**, and **Visa**.

## Overview

This agent uses **TF-IDF text retrieval** and **keyword-based classification** to:
1. Identify the company/product domain
2. Classify the request type (bug, billing, feature_request, etc.)
3. Determine the product area within that domain
4. Decide whether to reply with a grounded answer or escalate to a human
5. Generate a response grounded in the provided support corpus

## Architecture

### Pipeline Flow

```
Input CSV → normalize_company() → domain_key()
           ↓
        TF-IDF retrieval (CorpusRetriever)
           ↓
    classify_request_type() + classify_product_area()
           ↓
    decide_status() [escalation logic]
           ↓
    grounded_response() [snippet extraction]
           ↓
    Output CSV
```

### Components

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point, orchestrates the pipeline, reads input CSV, writes output CSV |
| `retriever.py` | TF-IDF-based corpus retrieval; loads markdown/text docs, chunks them, searches by query |
| `classifier.py` | Domain/company inference, request type classification, product area routing |
| `safety.py` | High-risk term detection, confidence-based escalation logic |
| `response_generator.py` | Extracts best snippet from retrieved docs, formats user-facing response |

### Key Design Decisions

1. **TF-IDF over embeddings**: Deterministic, reproducible, no API calls, faster inference, suitable for this corpus size
2. **Aggressive escalation**: Any high-risk term (fraud, payment, security) → escalate; any confidence < 0.12 → escalate
3. **Rule-based classification**: Keyword matching over ML models (fast, interpretable, no training data needed)
4. **No external LLMs**: All logic is self-contained, fully auditable

### Known Limitations & Trade-offs

- **Single-turn stateless**: Each ticket is processed independently; no multi-turn conversation support
- **No sentiment analysis**: Treats angry and calm queries identically
- **Conservative escalations**: Some legitimate requests may escalate if they contain high-risk keywords
- **Snippet quality**: Response quality depends on corpus quality and query/doc relevance

## Installation

### Requirements
- Python 3.8+
- pandas >= 3.0.0
- scikit-learn >= 1.8.0
- numpy (installed as dependency)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, sklearn; print('OK')"
```

## Usage

### Basic Usage

```bash
python main.py \
  --corpus ../data \
  --input ../support_tickets/support_tickets.csv \
  --output ../support_tickets/output.csv \
  --log agent.log
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--corpus` | `../data` | Path to support corpus folder (HackerRank, Claude, Visa docs) |
| `--input` | `support_tickets.csv` | Input CSV file with columns: Issue, Subject, Company |
| `--output` | `output.csv` | Output CSV file with predicted columns |
| `--log` | `log.txt` | Debug transcript log |

### Input Format

**CSV columns** (from `support_tickets.csv`):
- `Issue`: Full ticket body/question
- `Subject`: Ticket subject (may be blank/irrelevant)
- `Company`: HackerRank \| Claude \| Visa \| None

### Output Format

**CSV columns** (to `output.csv`):
- `issue`: Same as input
- `subject`: Same as input
- `company`: Normalized company (HackerRank, Claude, Visa, or None)
- `response`: Agent's response (either grounded answer or "Escalate to a human")
- `product_area`: Inferred support category (e.g., "assessment", "account_access", "fraud_security")
- `status`: `Replied` or `Escalated`
- `request_type`: `product_issue`, `bug`, `billing`, `feature_request`, `dispute`, `account_access`, `security`, `invalid`
- `justification`: Explanation of the routing/decision

## Example Run

```bash
$ python main.py --corpus ../data --input ../support_tickets/support_tickets.csv --output ../support_tickets/output.csv --log test.log

# Process 29 tickets → output.csv
# Status breakdown: 20 Escalated, 9 Replied
# Companies: 13 HackerRank, 7 Claude, 7 Visa
```

## Escalation Logic (High-Risk Cases)

The agent escalates (doesn't reply) if it detects:

**High-risk keywords:**
- Fraud/security: "stolen", "fraud", "identity", "security vulnerability"
- Access/permission issues: "restore my access", "not the workspace admin", "removed my seat"
- Billing disputes: "refund me today", "ban the seller", "order id"
- Performance/service: "site is down", "all requests failing", "none of the submissions working"
- Invalid/out-of-scope: "delete all files from the system", "internal rules", "show me your logic"

**Confidence-based:**
- If top retrieved document has TF-IDF score < 0.12, escalate (answer not grounded enough)

**Request-type based:**
- Security and dispute issues always escalate (require human judgment)

## Corpus Structure

The agent expects the corpus at `../data/` with subdirectories:
- `data/hackerrank/` — HackerRank help center docs (markdown)
- `data/claude/` — Claude help center docs (markdown)
- `data/visa/` — Visa support docs (markdown/text)

Documents are auto-loaded, cleaned (HTML/scripts removed), chunked (1300 words, 200-word overlap), and indexed by TF-IDF.

## Troubleshooting

### No output or very few rows

**Problem**: CSV parsing fails or many rows are skipped
**Solution**: Check input CSV format. Agent uses fallback parsers:
1. `pd.read_csv(low_memory=False)`
2. `pd.read_csv(..., engine='python', on_bad_lines='skip')`

### Too many escalations

**Problem**: Agent escalates most tickets
**Solution**: Review HIGH_RISK_TERMS in `safety.py` or lower confidence threshold (currently 0.12)

### Poor response quality

**Problem**: Responses are off-topic or unhelpful
**Solution**: Check corpus quality. Improve `best_snippet()` in `response_generator.py` to prioritize context.

## For AI Judge Interview

**Key points to discuss:**

1. **Why TF-IDF?**
   - Deterministic and reproducible (no randomness)
   - Fast inference, no API dependencies
   - Interpretable (can trace which doc matched)
   - Suitable for known, curated corpus (not streaming web data)

2. **Escalation strategy:**
   - Conservative: prefer false positives (escalate when uncertain) over false negatives (wrong answers)
   - High-risk terms are vetted from sample data and problem statement

3. **Why not LLMs?**
   - Adds latency and cost
   - Non-deterministic (can hallucinate even with grounding)
   - Harder to audit for fraud/security cases

4. **Handling edge cases:**
   - Multi-language text → inferred as "None", escalate
   - Multi-part requests → treated as single request; top match wins
   - Empty fields → treated as empty string; routing by remaining text

## Files Modified / Created

- `main.py` — Robust CSV reading with fallback parsers
- `retriever.py`, `classifier.py`, `safety.py`, `response_generator.py` — (No modifications, already complete)
- `requirements.txt` — (Already contains pandas, scikit-learn)
- `README.md` — **This file** (architecture & runbook)

## Next Steps for Improvement

1. **Hybrid retrieval**: Combine TF-IDF with dense embeddings for better recall
2. **Feedback loop**: Collect human corrections, retrain classifier
3. **Context awareness**: Track conversation history (multi-turn support)
4. **Auto-categorization**: Learn domain-specific keywords from corpus
5. **A/B testing**: Compare rule-based vs LLM-based responses on hold-out set
