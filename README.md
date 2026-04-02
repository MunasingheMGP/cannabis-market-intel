# 🌿 MontKailash Cannabis — Market Intelligence Pipeline

> A fully automated 7-step Python pipeline that collects, enriches, and scores cannabis retail intelligence for Burlington, Ontario (35 km radius). Outputs a polished Excel pack and PDF strategy report — no paid APIs required.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Output Files](#output-files)
- [Known Limitations](#known-limitations)
- [Disclaimer](#disclaimer)

---

## Overview

This pipeline answers six business questions for a cannabis retailer entering or competing in the Burlington, ON market:

1. **How many licensed stores operate within 35 km?** (AGCO registry)
2. **What are their contact details and hours?** (web scraping)
3. **What products and prices do competitors carry?** (BestBangForYourBud)
4. **How do those prices compare to HiBuddy.ca and OCS.ca?** (multi-source comparison)
5. **What is the market sentiment and velocity for each product?** (Reddit + analytics)
6. **Which products should be prioritised — and what action should be taken?** (scoring engine)

---

## Pipeline Architecture

```
step1.py  →  AGCO store list (35 km radius, Burlington ON)
    ↓
step2.py  →  Enrich with phone + hours (web scraping)
    ↓
step3.py  →  Competitor product catalogue + pricing (BestBangForYourBud)
    ↓
step4.py  →  Market price comparison (HiBuddy + OCS Shopify API)
    ↓
step5.py  →  Reddit brand sentiment + business analytics summary
    ↓
step6.py  →  Priority scoring + executive actionable insights
    ↓
step7.py  →  Final Excel intelligence pack + PDF strategy report
```

All intermediate results are cached in `/output/` — re-running any step does not re-fetch already-collected data.

---

## Requirements

- Python 3.10+
- Node.js (only if regenerating this README or docs — not required to run pipeline)

### Python Dependencies

```
pandas
requests
beautifulsoup4
lxml
openpyxl
reportlab
```

Install all at once:

```bash
pip install pandas requests beautifulsoup4 lxml openpyxl reportlab
```

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/montkailash-intelligence.git
cd montkailash-intelligence
pip install pandas requests beautifulsoup4 lxml openpyxl reportlab
```

---

## Usage

### Run the full pipeline sequentially

```bash
python step1.py   # ~30 seconds
python step2.py   # ~5–10 minutes (scrapes each store website)
python step3.py   # ~3–5 minutes
python step4.py   # ~5–10 minutes (HiBuddy + OCS)
python step5.py   # ~10–20 minutes (Reddit, rate-limit safe)
python step6.py   # ~5 seconds
python step7.py   # ~10 seconds
```

### Configuration (step1.py)

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
| `stores_master.csv` | Licensed stores within 35 km | step1 + step2 |
| `products_pricing_snapshot.csv` | Competitor product catalogue with pricing | step3 |
| `bbfyb_stores.csv` | BestBangForYourBud store cross-reference | step3 |
| `hibuddy_raw.csv` | Raw HiBuddy.ca prices (cached) | step4 |
| `ocs_raw.csv` | OCS full product catalogue (cached) | step4 |
| `market_comparison.csv` | Price delta vs OCS and HiBuddy | step4 |
| `reddit_sentiment_raw.csv` | Per-brand Reddit sentiment (cached) | step5 |
| `business_analytics_summary.csv` | Sales velocity, sell-through, pricing frequency | step5 |
| `executive_actionable_insights.csv` | Priority scores + strategic actions | step6 |
| `MontKailash_Executive_Insight_Pack.xlsx` | Multi-tab Excel pack with conditional formatting | step7 |
| `MontKailash_Strategy_Report.pdf` | Branded PDF report with top 10 opportunities | step7 |

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
| Reddit `/search.json` may rate-limit heavy usage | Sentiment data incomplete | Use official PRAW library with OAuth |
| Store owner details are marked "Not publicly disclosed" | Ownership data missing | Cross-reference Ontario Business Registry |
| Phone/hours rely on website structure | ~60–80% fill rate expected | Supplement with Google Places API |
| No automated scheduler | Manual re-run required | Add cron job or GitHub Actions workflow |

---

## Disclaimer

This tool is intended for legitimate competitive market research. All data is collected from publicly accessible sources. Respect each website's `robots.txt` and terms of service. The built-in request delays are intentional — do not remove them.

---

## License

MIT License — free to use and modify for commercial and non-commercial purposes.
