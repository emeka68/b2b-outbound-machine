# 🚀 B2B Outbound Machine

A **production-ready Python CLI tool** that replicates [Clay.com](https://clay.com)'s B2B outbound automation workflows. Enrich leads → Score buying signals → Generate personalized icebreakers → Export to Lemlist.

**Built as a portfolio piece** to land Clay/Lemlist automation jobs on Upwork.

---

## What It Does

Takes a CSV of company names/domains and transforms it into a ready-to-import Lemlist campaign:

```
Input: leads.csv
  ↓ [Enricher: Web scraping + tech stack detection]
  ↓ [Signal Detector: DPP compliance & commerce platform scoring]
  ↓ [Personalizer: AI-powered icebreaker generation]
  ↓ [Lemlist Exporter: Filter & format for bulk import]
Output: lemlist_import_YYYY-MM-DD.csv ✅
```

### Key Features

✅ **Web Enrichment**
  - Scrapes company websites for tech stack (Shopware, Magento, WooCommerce, SAP, etc.)
  - Detects DPP compliance signals (EU regulation readiness)
  - Extracts industry, company size, and description snippets

✅ **Intelligent Scoring**
  - DPP Signal Score (0-100): Measures digital product passport compliance readiness
  - Commerce Signal Score (0-100): Detects legacy platforms & modernization needs
  - Priority tiers: HOT (urgent) / WARM (nurture) / COLD (research)

✅ **AI Personalization**
  - OpenAI integration for hyper-personalized email icebreakers
  - Falls back to template-based personalization if no API key
  - Two campaign types: DPP compliance solutions & B2B commerce modernization

✅ **Lemlist-Ready Export**
  - Native CSV format for Lemlist bulk import
  - Filters by minimum score threshold
  - Campaign-specific messaging

✅ **Zero Cost to Run**
  - Self-hosted (no Clay.com SaaS fees)
  - Only cost: ~$0.10 per 100 leads for OpenAI (optional)
  - Works without OpenAI key (template fallback)

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/emeka68/b2b-outbound-machine.git
cd b2b-outbound-machine

python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

pip install -r requirements.txt
```

### 2. Set Up (Optional)

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key (optional)
```

### 3. Run the Pipeline

```bash
python pipeline.py --input sample_leads.csv
```

Or with filters:

```bash
python pipeline.py \
  --input your_leads.csv \
  --output-dir ./results \
  --min-score 60 \
  --campaign DPP
```

### 4. Import to Lemlist

The final output (`lemlist_import_*.csv`) is ready for Lemlist's bulk import:

1. Open Lemlist → Create Campaign
2. Click "Import Leads"
3. Upload `lemlist_import_YYYY-MM-DD.csv`
4. Map columns (should auto-detect)
5. Start outreach 🚀

---

## CLI Usage

```bash
python pipeline.py --help

Options:
  --input TEXT              Input CSV file with company/domain data [required]
  --output-dir TEXT         Output directory for results (default: current)
  --min-score INTEGER       Min signal score to include (0-100, default: 0)
  --campaign [DPP|B2B_Commerce]  Filter by campaign type (optional)
  --help                    Show this message
```

### Examples

**Process all leads:**
```bash
python pipeline.py --input leads.csv
```

**Only export HOT leads with DPP signals:**
```bash
python pipeline.py --input leads.csv --min-score 70 --campaign DPP
```

**Only export WARM+ B2B Commerce leads:**
```bash
python pipeline.py --input leads.csv --min-score 40 --campaign B2B_Commerce
```

---

## Input CSV Format

Your input CSV must have these columns:

```csv
company,domain,contact_first,contact_last,email,title
MünchTech GmbH,munchtech.de,Klaus,Hoffmann,klaus.hoffmann@munchtech.de,CEO
Bavaria Manufacturing,bavaria-manufacturing.de,Anna,Schmidt,anna.schmidt@bavaria-manufacturing.de,Head of Operations
...
```

See `sample_leads.csv` for a template.

---

## Output Files

The pipeline creates 4 intermediate CSVs + 1 final export:

```
results/
├── 01_enriched_20240320_162530.csv      # Step 1: Tech stack & DPP signals
├── 02_scored_20240320_162530.csv        # Step 2: Buying signal scores
├── 03_personalized_20240320_162530.csv  # Step 3: AI icebreakers
└── 04_lemlist_import_20240320_162530.csv # Step 4: Ready for Lemlist ✅
```

Each CSV retains all previous data + new columns, so you can inspect the enrichment at each stage.

---

## Architecture

### Module Breakdown

#### **enricher.py** — Web Scraping & Data Enrichment
- HTTP fetching with retry logic
- BeautifulSoup HTML parsing
- Tech stack detection (platform identifiers)
- DPP compliance signal extraction
- Industry classification
- Rate limiting (0.5s between requests)

#### **signal_detector.py** — Buying Signal Scoring
- DPP Signal Score: 0-100 based on compliance readiness
- Commerce Signal Score: 0-100 based on legacy platform detection
- Priority determination: HOT (≥70) / WARM (≥40) / COLD (<40)
- Campaign recommendation: DPP vs B2B_Commerce

#### **personalizer.py** — AI Personalization
- OpenAI Chat Completions integration (default `gpt-4o-mini`) for dynamic copy
- Two campaign templates (DPP + Commerce)
- Fallback template-based personalization (no API)
- Error handling with graceful degradation

#### **lemlist_export.py** — Campaign Export
- Field mapping to Lemlist schema
- Filtering by minimum score & campaign type
- Timestamped CSV output
- Summary statistics

#### **pipeline.py** — Orchestration
- Runs all 4 modules in sequence
- CLI interface with Click
- Progress logging
- Summary reporting

---

## Clay.com Architecture Mapping

This project **replicates Clay's workflow architecture** in Python. See `clay_workflow_architecture.md` for detailed comparisons:

- **Enrichment Step** → Clay's Web Scraper + Regex Extract blocks
- **Signal Detection** → Clay's Formula fields + Conditional logic
- **Personalization** → Clay's OpenAI Claygent block
- **Export** → Clay's CSV export + Field mapper

Understanding this code = understanding Clay's value proposition.

---

## OpenAI Integration (Optional)

### With API Key ✅

If you set `OPENAI_API_KEY` in `.env`, the personalizer uses OpenAI's Chat Completions API for dynamic icebreakers:

```python
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # optional, this is the default
```

Cost: ~$0.001 per 1000 tokens (~$0.10 per 100 leads)

### Without API Key ✅

If no key is set, falls back to template-based personalization:

```python
# Template: "We noticed {company} is focused on {signals}. With EU's..."
```

**Both modes work perfectly.** Templates are designed to be engaging and conversion-tested.

---

## Signal Scoring Details

### DPP Signal Score

Looks for compliance-related keywords:
- "digital product passport"
- "EU compliance"
- "sustainability"
- "traceability"
- "circular economy"
- "product data"

**Use case:** Companies preparing for EU regulations. Target: manufacturers in German-speaking regions.

### Commerce Signal Score

Detects legacy platforms:
- Magento (legacy e-commerce)
- WooCommerce (outdated WordPress)
- PrestaShop (dated platform)
- SAP (legacy ERP)

**Use case:** Companies due for modernization. Target: SMBs with technical debt.

### Priority Tiers

| Tier | Score | Action |
|------|-------|--------|
| **HOT** | ≥70 | Immediate outreach, personalized call |
| **WARM** | 40-69 | Nurture sequence, sequence 2x/week |
| **COLD** | <40 | Research phase, low priority |

---

## Recommended Campaigns

### DPP Campaign
**Best for:** Manufacturing, logistics, wholesale
**Pitch:** "Help ensure EU Digital Product Passport compliance"
**Timeline:** 3-6 months (regulatory pressure)
**Decision maker:** Chief Operations Officer, Compliance Manager

### B2B Commerce Campaign
**Best for:** E-commerce, B2B platforms, online retailers
**Pitch:** "Modernize from legacy platforms (Magento, SAP) to flexible solutions"
**Timeline:** 6-12 months (strategic project)
**Decision maker:** CTO, VP Engineering, CEO

---

## Troubleshooting

### Pipeline hangs on enrichment
- Check internet connectivity
- Some websites may be blocking automated requests
- Increase timeout in `enricher.py`: `CompanyEnricher(timeout=15)`

### OpenAI API errors
- Verify `OPENAI_API_KEY` is valid
- Check your OpenAI billing at https://platform.openai.com/account/billing
- Pipeline automatically falls back to templates on error

### No enriched data / "N/A" in results
- Website may not be accessible or blocks scraping
- Missing meta tags or description
- This is normal for some sites; manual review is recommended

### Lemlist import fails
- Check column headers match Lemlist's schema
- Ensure email addresses are valid
- Max 5000 leads per import (split into batches if needed)

---

## Performance & Scaling

**Typical performance on sample_leads.csv (5 leads):**
- Enrichment: 2-5 seconds per lead (HTTP request + parsing)
- Signal detection: <1 second for all leads
- Personalization: 1-2 seconds per lead (with OpenAI) or <100ms (templates)
- **Total:** ~5-15 seconds for 5 leads

**Scaling to 1000 leads:**
- Estimate: 2-3 hours
- Recommend: Run as background job (nohup, cron, k8s)
- Consider: Rate limiting to avoid getting blocked by target websites

**For production use:**
- Deploy to cloud (AWS Lambda, GCP Cloud Functions, Heroku)
- Set up scheduling (cron, APScheduler)
- Monitor logs & export to data warehouse
- Add database persistence for incremental updates

---

## Cost Analysis

| Component | Cost |
|-----------|------|
| This tool (self-hosted) | $0 |
| AWS/GCP compute (~1000 leads/month) | $5-20 |
| OpenAI API (~1000 leads/month) | $0-10 |
| **Total** | **$5-30/month** |

vs.

| Component | Cost |
|-----------|------|
| Clay.com (~1000 leads/month) | $200-500 |
| Lemlist (contact limit) | $50-300 |
| **Total** | **$250-800/month** |

**ROI:** Build once, save thousands/month on Clay licensing.

---

## Advanced Usage

### Custom Signal Detection

Edit `signal_detector.py` to add your own scoring logic:

```python
# signal_detector.py
DPP_COMPLIANCE_KEYWORDS = [
    'your-custom-keyword',
    'your-industry-signal',
    # ...
]
```

### Custom Enrichment Data

Add new columns in `enricher.py`:

```python
# enricher.py
def enrich_row(self, row):
    # Add custom scraping logic
    linkedin_url = self.fetch_linkedin_profile(row['domain'])
    return {**row, 'linkedin_url': linkedin_url, ...}
```

### Direct API Calls

For production, add Lemlist API integration:

```python
# lemlist_export.py
from lemlist import LemlistAPI

client = LemlistAPI(api_key=os.getenv('LEMLIST_API_KEY'))
client.create_campaign('DPP Campaign', leads_df)
```

---

## Security

⚠️ **Never commit `.env` with real API keys**

```bash
# .gitignore
.env
.env.local
*.pyc
__pycache__/
venv/
```

We've already added `.env` to `.gitignore` in the git repo.

---

## Contributing

This is a portfolio project. Feel free to fork and customize for your own use case.

**Suggested enhancements:**
- [ ] Database persistence (SQLite, PostgreSQL)
- [ ] Lemlist API direct integration
- [ ] LinkedIn scraping (with API)
- [ ] Email validation service (NeverBounce, ZeroBounce)
- [ ] Slack notifications on high-priority leads
- [ ] Web UI dashboard (Flask/Streamlit)
- [ ] Scheduled runs (APScheduler, Celery)

---

## About

**Author:** Nnaemeka Duru  
**Email:** emekaduru09@gmail.com  
**Purpose:** Portfolio piece for Clay.com/Lemlist automation consulting  
**License:** MIT (feel free to use, modify, sell services built on this)

---

## Support

**Issues?**
- Check the troubleshooting section above
- Review logs (each step logs to console)
- Test with `sample_leads.csv` first

**Want to use this professionally?**
- Reference this in job applications
- Link to the GitHub repo as proof of skill
- Customize for client use cases
- Pitch as "Clay.com alternative for cost-conscious teams"

---

## Next Steps

1. ✅ Run with sample data: `python pipeline.py --input sample_leads.csv`
2. ✅ Inspect the 4 output CSVs to understand the transformation
3. ✅ Try with your own leads CSV
4. ✅ Set up OpenAI API key for AI-powered icebreakers
5. ✅ Import results to Lemlist and launch campaign
6. ✅ Track performance and iterate

**Good luck with your outbound! 🚀**

---

_Built with ❤️ for modern B2B sales teams_
