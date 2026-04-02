"""
Run the full MontKailash pipeline end to end.
"""

import subprocess
import sys
import time
from pathlib import Path

STEPS = [
    ("fetch_stores_agco.py",          "Fetching licensed stores from AGCO registry"),
    ("enrich_store_contacts.py",       "Enriching stores with phone numbers and hours"),
    ("scrape_competitor_products.py",  "Scraping competitor products and pricing"),
    ("compare_market_prices.py",       "Comparing prices against HiBuddy and OCS"),
    ("reddit_sentiment_analytics.py",  "Fetching Reddit sentiment and building analytics"),
    ("score_product_insights.py",      "Scoring products and generating insights"),
    ("export_reports.py",              "Exporting Excel pack and PDF report"),
]


def run_step(script: str, description: str, step_num: int, total: int):
    print(f"\n{'='*60}")
    print(f"  Step {step_num}/{total} — {description}")
    print(f"  Running: {script}")
    print(f"{'='*60}")

    start = time.time()
    result = subprocess.run([sys.executable, script], check=False)
    elapsed = round(time.time() - start, 1)

    if result.returncode != 0:
        print(f"\nStep {step_num} FAILED ({script}) after {elapsed}s")
        print("   Fix the error above and re-run from this step.")
        sys.exit(result.returncode)

    print(f"\nStep {step_num} done in {elapsed}s")


def main():
    print("\n MontKailash Cannabis — Full Pipeline")
    print(f"    {len(STEPS)} steps | Output -> ./output/\n")

    # check all scripts exist before starting
    missing = [s for s, _ in STEPS if not Path(s).exists()]
    if missing:
        print(" Missing files:")
        for m in missing:
            print(f"    - {m}")
        sys.exit(1)

    total_start = time.time()

    for i, (script, description) in enumerate(STEPS, 1):
        run_step(script, description, i, len(STEPS))

    total = round(time.time() - total_start, 1)
    print(f"\n{'='*60}")
    print(f"  All {len(STEPS)} steps completed in {total}s")
    print(f"  Output files -> ./output/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()