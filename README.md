# 🌿 MontKailash Cannabis — Market Intelligence Pipeline

> A fully automated Python pipeline that collects, enriches, and scores cannabis retail intelligence for Burlington, Ontario (35 km radius). Outputs a polished Excel pack and PDF strategy report — no paid APIs required.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Output Files](#output-files)
- [Data Sources](#data-sources)
- [Known Limitations](#known-limitations)
- [Disclaimer](#disclaimer)

---

## Overview

This pipeline answers six business questions for a cannabis retailer entering or competing in the Burlington, ON market:

1. **How many licensed stores operate within 35 km?** — AGCO registry
2. **What are their contact details and hours?** — web scraping
3. **What products and prices do competitors carry?** — BestBangForYourBud
4. **How do those prices compare to HiBuddy.ca and OCS.ca?** — multi-source comparison
5. **What is the market sentiment and velocity for each product?** — Reddit + analytics
6. **Which products should be prioritised — and what action should be taken?** — scoring engine

---

## Pipeline Architecture

```
fetch_stores_agco.py           →  AGCO store list (35 km radius, Burlington ON)
    ↓
enrich_store_contacts.py       →  Enrich with phone + hours (web scraping)
    ↓
scrape_competitor_products.py  →  Competitor product catalogue + pricing (BestBangForYourBud)
    ↓
compare_market_prices.py       →  Market price comparison (HiBuddy + OCS Shopify API)
    ↓
reddit_sentiment_analytics.py  →  Reddit brand sentiment + business analytics summary
    ↓
score_product_insights.py      →  Priority scoring + executive actionable insights
    ↓
export_reports.py              →  Final Excel intelligence pack + PDF strategy report
```

All intermediate results are cached in `/output/` — re-running any step does not re-fetch already-collected data.

---

## Requirements

- Python 3.10+

### Python Dependencies

```
pandas>=1.5.0
requests>=2.28.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
openpyxl>=3.1.0
reportlab>=4.0.0
```

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/cannabis-market-intel.git
cd cannabis-market-intel
pip install -r requirements.txt
```

---

## Usage

### Run the full pipeline (recommended)

```bash
python run_all.py
```

This runs all 7 steps in sequence, shows progress and timing per step, and stops immediately if any step fails.

### Run individual steps

```bash
python fetch_stores_agco.py           # ~30 seconds
python enrich_store_contacts.py       # ~5–10 minutes
python scrape_competitor_products.py  # ~3–5 minutes
python compare_market_prices.py       # ~5–10 minutes
python reddit_sentiment_analytics.py  # ~10–20 minutes (rate-limit safe)
python score_product_insights.py      # ~5 seconds
python export_reports.py              # ~10 seconds
```

### Configuration (`fetch_stores_agco.py`)

| Variable | Default | Description |
|---|---|---|
| `CENTER_LAT` | `43.3255` | Burlington, ON latitude |
| `CENTER_LON` | `-79.7990` | Burlington, ON longitude |
| `RADIUS_KM` | `35` | Search radius in kilometres |

---

## Output Files

All files are written to the `/output/` directory.

| File | Description | Created by |
|---|---|---|
| `stores_master.csv` | Licensed stores within 35 km with phone + hours | fetch + enrich |
| `products_pricing_snapshot.csv` | Competitor product catalogue with pricing | scrape_competitor |
| `bbfyb_stores.csv` | BestBangForYourBud store cross-reference | scrape_competitor |
| `hibuddy_raw.csv` | Raw HiBuddy.ca prices (cached) | compare_market |
| `ocs_raw.csv` | OCS full product catalogue (cached) | compare_market |
| `market_comparison.csv` | Price delta vs OCS and HiBuddy | compare_market |
| `reddit_sentiment_raw.csv` | Per-brand Reddit sentiment (cached) | reddit_sentiment |
| `business_analytics_summary.csv` | Sales velocity, sell-through, pricing frequency | reddit_sentiment |
| `executive_actionable_insights.csv` | Priority scores + strategic actions | score_insights |
| `MontKailash_Executive_Insight_Pack.xlsx` | Multi-tab Excel pack with conditional formatting | export_reports |
| `MontKailash_Strategy_Report.pdf` | Branded PDF report with top 10 opportunities | export_reports |

---

## Data Sources

| Source | Data Collected | Method |
|---|---|---|
| [AGCO ArcGIS](https://services9.arcgis.com/8LLh665FxwX7bxLB/arcgis/rest/services) | Licensed store locations | REST API (free) |
| Store websites | Phone numbers, hours of operation | HTML scraping |
| [BestBangForYourBud.ca](https://bestbangforyourbud.com) | Competitor product listings + prices | HTML scraping |
| [HiBuddy.ca](https://hibuddy.ca) | Competitor pricing | HTML scraping |
| [OCS.ca](https://ocs.ca) | Provincial product catalogue + prices | Shopify JSON API (free) |
| [r/OntarioCannabis](https://reddit.com/r/OntarioCannabis) | Brand sentiment, post count, upvotes | Reddit JSON API (free) |

---

## Known Limitations

| Limitation | Impact | Suggested Fix |
|---|---|---|
| BBFYB/HiBuddy CSS selectors may break if site updates | Products not scraped | Switch to Playwright for JS-rendered pages |
| Reddit `/search.json` may rate-limit heavy usage | Sentiment data incomplete | Use PRAW library with OAuth |
| Store owner details marked "Not publicly disclosed" | Ownership data missing | Cross-reference Ontario Business Registry |
| Phone/hours rely on website structure | ~60–80% fill rate expected | Supplement with Google Places API |
| No automated scheduler | Manual re-run required | Add cron job or GitHub Actions workflow |

---

## Project Structure

```
cannabis-market-intel/
├── run_all.py                        ← run full pipeline
├── fetch_stores_agco.py
├── enrich_store_contacts.py
├── scrape_competitor_products.py
├── compare_market_prices.py
├── reddit_sentiment_analytics.py
├── score_product_insights.py
├── export_reports.py
├── requirements.txt
├── README.md
└── output/                           ← all generated files (git ignored)
```

---

## Disclaimer

This tool is intended for legitimate competitive market research. All data is collected from publicly accessible sources. Respect each website's `robots.txt` and terms of service. The built-in request delays are intentional — do not remove them.

---

## License

MIT License — free to use and modify for commercial and non-commercial purposes.