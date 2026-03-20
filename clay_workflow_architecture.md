# Clay.com Workflow Architecture

## Overview

This B2B outbound automation pipeline replicates the workflow patterns used by Clay.com for data enrichment, signal detection, and personalized outreach campaigns. Below is a detailed mapping between this project's Python implementation and Clay's visual workflow builder.

---

## Full Workflow Diagram

```
[Input: CSV with Company List]
           ↓
    ┌─────────────────┐
    │  ENRICHMENT     │
    │  (enricher.py)  │
    └────────┬────────┘
             ↓ [Enriched Data: Tech Stack, DPP Signals]
    ┌─────────────────────────────┐
    │   SIGNAL DETECTION          │
    │  (signal_detector.py)       │
    │  - DPP Score: 0-100         │
    │  - Commerce Score: 0-100    │
    │  - Priority: HOT/WARM/COLD  │
    └────────┬────────────────────┘
             ↓ [Scored Leads]
    ┌──────────────────────────────────┐
    │  PERSONALIZATION                 │
    │  (personalizer.py)               │
    │  - AI Icebreaker (OpenAI API)    │
    │  - Fallback Templates (no API)   │
    └────────┬─────────────────────────┘
             ↓ [Personalized Icebreakers]
    ┌─────────────────────────────┐
    │   LEMLIST EXPORT            │
    │  (lemlist_export.py)        │
    │  Filter by Score & Campaign │
    └────────┬────────────────────┘
             ↓
    [Output: lemlist_import_YYYY-MM-DD.csv]
```

---

## Step 1: ENRICHMENT (enricher.py)

### What It Does
Scrapes company websites and extracts structured data signals.

### Clay Equivalent

In Clay, this would be implemented as a **Waterfall with Web Scraper + HTTP Requests**:

```
┌─ Clay Table: "Companies" ─────────────────┐
│  Columns:                                  │
│  - company_name                            │
│  - domain                                  │
│  - contact_first                           │
│  - contact_last                            │
│  - email                                   │
│  - title                                   │
└────────────────────────────────────────────┘
         ↓
┌─ Claygent: "Website Scraper" ───────────────────────────────┐
│  1. Fetch Page (HTTP GET)                                    │
│     Input: domain                                            │
│     Output: raw_html                                         │
│  2. Parse Meta Tags (Regex/Extract)                          │
│     Extract: title, meta description, og:description         │
│  3. Detect Tech Stack (Search Keywords)                      │
│     Look for: Shopware, Magento, WooCommerce, SAP, etc.      │
│  4. Extract Body Text (HTML Parser)                          │
│     Extract: first 500 characters                            │
└──────────────────────────────────────────────────────────────┘
         ↓
┌─ Waterfall Result Columns ──────────────────────┐
│ - tech_stack (comma-separated)                  │
│ - description_snippet (first 200 chars)         │
│ - dpp_ready (0-100 score)                       │
│ - signals_found (compliance keywords)           │
│ - industry (detected from content)              │
└─────────────────────────────────────────────────┘
```

### Key Clay Components
- **Web Scraper** (HTTP GET) → fetch company website
- **Regex Extract** → parse meta tags and detect tech stack
- **Keyword Search** → find DPP compliance signals ("digital product passport", "EU compliance", "sustainability")
- **Text Parser** → extract description snippets

### In Python
The `enricher.py` module encapsulates:
1. HTTP requests with retry logic (Clay's HTTP blocks)
2. BeautifulSoup parsing (Clay's Text Parser)
3. Regex/keyword matching (Clay's Search/Extract blocks)
4. Rate limiting (0.5s between requests)

---

## Step 2: SIGNAL DETECTION (signal_detector.py)

### What It Does
Scores leads based on their enriched data and determines buying signals.

### Clay Equivalent

In Clay, this would be a **Calculation/Formula Claygent**:

```
┌─ Input Table: "Enriched Companies" ──────────┐
│ (from Step 1 enrichment)                      │
│ - tech_stack                                  │
│ - dpp_ready                                   │
│ - signals_found                               │
│ - industry                                    │
└──────────────────────────────────────────────┘
         ↓
┌─ Claygent: "Signal Scorer" ──────────────────────────────────────┐
│                                                                   │
│ Formula 1: DPP_SIGNAL_SCORE                                       │
│   IF (dpp_ready > 0) THEN                                         │
│     score = dpp_ready +                                           │
│     (count_of_compliance_keywords_in_signals * 10)                │
│   ELSE score = 0                                                  │
│   RESULT: 0-100 (capped)                                          │
│                                                                   │
│ Formula 2: COMMERCE_SIGNAL_SCORE                                  │
│   legacy_platforms = ["magento", "woocommerce", "prestashop"]     │
│   detected_count = COUNT(tech_stack CONTAINS legacy_platforms)    │
│   score = detected_count * 25                                     │
│   RESULT: 0-100 (capped)                                          │
│                                                                   │
│ Formula 3: PRIORITY (Conditional)                                 │
│   IF MAX(DPP_SIGNAL_SCORE, COMMERCE_SIGNAL_SCORE) >= 70 THEN     │
│     priority = "HOT"                                              │
│   ELSE IF >= 40 THEN                                              │
│     priority = "WARM"                                             │
│   ELSE                                                            │
│     priority = "COLD"                                             │
│                                                                   │
│ Formula 4: RECOMMENDED_CAMPAIGN                                   │
│   IF DPP_SIGNAL_SCORE > COMMERCE_SIGNAL_SCORE THEN               │
│     campaign = "DPP"                                              │
│   ELSE                                                            │
│     campaign = "B2B_Commerce"                                     │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
         ↓
┌─ Output Columns ──────────────────────────────┐
│ - dpp_signal_score                            │
│ - commerce_signal_score                       │
│ - priority (HOT/WARM/COLD)                    │
│ - recommended_campaign                        │
└───────────────────────────────────────────────┘
```

### Key Clay Components
- **Formula Fields** → calculate scores using IF/THEN logic
- **COUNT/SEARCH** → find keyword matches
- **MAX() function** → determine priority tier

### In Python
The `signal_detector.py` module encapsulates:
1. Score calculation logic (mimics Clay formula fields)
2. Threshold-based prioritization
3. Conditional campaign recommendation

---

## Step 3: PERSONALIZATION (personalizer.py)

### What It Does
Generates hyper-personalized email icebreakers using AI (OpenAI) or fallback templates.

### Clay Equivalent

In Clay, this would be an **OpenAI Claygent** with fallback templates:

```
┌─ Input Table: "Scored Leads" ────────────────────────┐
│ - company                                            │
│ - tech_stack                                         │
│ - industry                                           │
│ - signals_found                                      │
│ - dpp_signal_score                                   │
│ - recommended_campaign                               │
└──────────────────────────────────────────────────────┘
         ↓
┌─ Claygent: "AI Icebreaker Generator" ────────────────────────────┐
│                                                                   │
│ IF (OPENAI_API_KEY is configured) THEN                            │
│   Use OpenAI GPT-3.5 Chat Completion:                             │
│   Prompt = '''                                                    │
│     Generate a compelling 2-3 sentence cold email icebreaker.     │
│     Company: {company}                                            │
│     Industry: {industry}                                          │
│     Tech Stack: {tech_stack}                                      │
│     Signals: {signals_found}                                      │
│     Campaign: {recommended_campaign}                              │
│   '''                                                             │
│   Result: personalized_icebreaker (150 tokens max)                │
│                                                                   │
│ ELSE (Fallback if no API)                                         │
│   Use Template-Based Generation:                                  │
│   IF (recommended_campaign == "DPP") THEN                         │
│     Template: "We noticed {company} is focused on                 │
│     {signal1}. With EU's Digital Product Passport mandate,        │
│     we're helping {industry} companies build compliance-ready     │
│     systems. Can we schedule a brief call?"                       │
│   ELSE                                                            │
│     Template: "{company} is running {tech_stack}. Modern          │
│     B2B buyers expect seamless integrations and APIs. We help     │
│     {industry} companies migrate in weeks, not months."           │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
         ↓
┌─ Output Column ───────────────┐
│ - icebreaker (AI or Template) │
└───────────────────────────────┘
```

### Key Clay Components
- **OpenAI Claygent** → Call GPT-3.5 for AI-generated copy
- **Conditional Logic** → fallback to templates if API fails
- **Template Variables** → inject company data into boilerplate

### In Python
The `personalizer.py` module encapsulates:
1. OpenAI API integration with error handling
2. Dynamic prompt building with company context
3. Fallback template-based personalization (no API required)
4. Two campaign types with different messaging strategies

---

## Step 4: LEMLIST EXPORT (lemlist_export.py)

### What It Does
Filters and exports personalized leads to Lemlist's native CSV import format.

### Clay Equivalent

In Clay, this would be a **Filter + Column Mapper + CSV Export**:

```
┌─ Input Table: "Personalized Leads" ────────────────────┐
│ (from Step 3 personalization)                          │
│ - All enriched + scored + personalized columns         │
└────────────────────────────────────────────────────────┘
         ↓
┌─ Claygent: "Lemlist Formatter" ──────────────────────────────────┐
│                                                                   │
│ Step 1: FILTER                                                    │
│   IF (composite_score >= min_score) AND                           │
│      (campaign == campaign_filter OR campaign_filter is NULL)     │
│   THEN include lead                                               │
│                                                                   │
│ Step 2: RENAME/MAP COLUMNS (Field Mapping)                        │
│   contact_first → firstName                                       │
│   contact_last → lastName                                         │
│   email → email                                                   │
│   company → companyName                                           │
│   domain → companyDomain                                          │
│   icebreaker → icebreaker                                         │
│   recommended_campaign → campaign                                 │
│   priority → priority                                             │
│   dpp_signal_score → dpp_signal_score                             │
│   commerce_signal_score → commerce_signal_score                   │
│                                                                   │
│ Step 3: SELECT COLUMNS (keep only Lemlist columns)                │
│   Drop: tech_stack, description_snippet, signals_found, etc.      │
│                                                                   │
│ Step 4: EXPORT AS CSV                                             │
│   Filename: lemlist_import_YYYY-MM-DD.csv                         │
│   Ready for Lemlist bulk import                                   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
         ↓
[Output: lemlist_import_YYYY-MM-DD.csv]
  Ready for: Lemlist Campaign Builder → Bulk Lead Import
```

### Key Clay Components
- **Filter Block** → conditional inclusion based on score/campaign
- **Column Mapper** → rename fields to Lemlist spec
- **CSV Export** → native Clay export functionality

### In Python
The `lemlist_export.py` module encapsulates:
1. Composite score calculation for filtering
2. Column mapping from internal schema to Lemlist format
3. Campaign/priority filtering with min score threshold
4. Timestamped CSV output

---

## Putting It All Together: The Main Pipeline (pipeline.py)

### Clay Equivalent: A Waterfall Workflow

In Clay's visual builder, this would be a single **Workflow** tab with 4 sequential steps:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAY WORKFLOW: "B2B Outbound"                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Input Table] ─→ [Enrichment Claygent] ─→ [Scoring Claygent]  │
│                                                                  │
│  ─→ [Personalization Claygent] ─→ [Lemlist Mapper] ─→ [Export] │
│                                                                  │
│  Triggers:                                                       │
│    • Run on CSV upload                                           │
│    • Schedule: Daily at 8am                                      │
│    • Manual trigger via UI button                                │
│                                                                  │
│  Parameters:                                                     │
│    • input_csv: "leads.csv"                                      │
│    • min_score: 60 (adjustable)                                  │
│    • campaign_filter: "DPP" or "B2B_Commerce" (optional)         │
│                                                                  │
│  Results:                                                        │
│    • 4 intermediate tables (enriched, scored, personalized)      │
│    • 1 final export table (lemlist_import)                       │
│    • Logs and statistics                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The Python `pipeline.py` is essentially a **headless/CLI version** of this Clay workflow:

```bash
python pipeline.py \
  --input leads.csv \
  --output-dir ./results \
  --min-score 60 \
  --campaign DPP
```

This produces the same result as clicking "Run Workflow" in Clay's UI.

---

## Key Differences: Python vs Clay

| Aspect | Python Implementation | Clay.com |
|--------|----------------------|----------|
| **Visual Design** | CLI + programmatic | Drag-and-drop UI builder |
| **Data Source** | CSV files | Tables (spreadsheet-like) |
| **Claygents** | Python classes | Visual Claygent blocks |
| **Web Scraping** | BeautifulSoup library | Built-in Web Scraper block |
| **Formulas** | Python functions | Formula fields with IF/THEN |
| **AI Integration** | Direct OpenAI API calls | OpenAI Claygent block |
| **Deployment** | Local CLI or cloud VM | SaaS (managed) |
| **Cost** | $0 (self-hosted) | $$ (per run/data) |
| **Customization** | Full code control | Limited to Clay's blocks |

---

## How to Use This for Clay Consulting

### 1. **Sell This as a Portfolio Piece**
   - Show how you replicated Clay's core architecture in Python
   - Demonstrate understanding of Clay's data flow: Enrichment → Scoring → Personalization → Export
   - Highlight cost savings (self-hosted vs Clay's pricing)

### 2. **Land Clay/Lemlist Jobs**
   - Interview answer: "I've built a Python equivalent of Clay's workflow. Here's how I'd architect your campaign..."
   - Show the mapping: "In Clay, your workflow would look like [diagram]. In Python, I implemented it with [architecture]."
   - Flexibility pitch: "For smaller teams or cost-sensitive clients, this Python version can run the same workflows for ~$100/mo in cloud hosting."

### 3. **Upwork Positioning**
   - Profile: "B2B Outbound Automation. Clay.com workflows in Python. Lemlist integration expert."
   - Package your services:
     - **Tier 1**: Use this tool to build Lemlist campaigns (+manual Clay workflows)
     - **Tier 2**: Customize the Python pipeline for client-specific signals
     - **Tier 3**: Deploy to their cloud infra with scheduling + monitoring

### 4. **Upgrade Path for Clients**
   - Start: "Use this Python tool to validate your outbound strategy (free/cheap)"
   - Upsell: "Once validated, let's set up a fully managed Clay.com workflow for scale"
   - Enterprise: "Custom Claygents + integrations for your specific B2B motion"

---

## API & Integration Points

### OpenAI API (Optional)
- Used in `personalizer.py` for AI icebreaker generation
- Requires: `OPENAI_API_KEY` in `.env`
- Model: `gpt-3.5-turbo`
- Cost: ~$0.001 per 1000 tokens (~$0.10 per 100 leads)
- Fallback: Template-based if API unavailable

### Lemlist API (Future Enhancement)
- Current: CSV export for manual import
- Future: Direct API integration to create campaigns programmatically
- Would need: Lemlist API key + campaign ID mapping

### Clay.com API (Future Enhancement)
- Could export directly to Clay workflows
- Would need: Clay API + auth + table mapping

---

## Summary

This Python project is a **complete implementation** of a modern B2B outbound workflow. It demonstrates:

1. **Data enrichment** (web scraping + parsing)
2. **Signal detection** (scoring + prioritization)
3. **AI personalization** (OpenAI integration)
4. **Campaign orchestration** (Lemlist export)

If you understand this codebase, you understand Clay.com's core value proposition — and you can sell/build variations of it.

---

*Author: Nnaemeka Duru (emekaduru09@gmail.com)*
*Built as a portfolio piece for Clay.com consulting & Lemlist automation jobs*
