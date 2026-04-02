"""
Score products and generate executive actionable insights.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# PATHS

OUTPUT_DIR    = Path("output")
SUMMARY_FILE  = OUTPUT_DIR / "business_analytics_summary.csv"
INSIGHTS_FILE = OUTPUT_DIR / "executive_actionable_insights.csv"



# PRIORITY SCORING

def priority_score(row) -> int:
    score = 0

    # Market penetration (0–3)
    ratio = float(row.get("presence_ratio", 0) or 0)
    if ratio >= 0.7:   score += 3
    elif ratio >= 0.4: score += 2
    else:              score += 1

    # Sell-through proxy (0–3)
    st = str(row.get("sell_through_proxy", ""))
    if st == "High":   score += 3
    elif st == "Medium": score += 2
    else:              score += 1

    # Reddit sentiment (0–3)
    sentiment = str(row.get("reddit_sentiment", ""))
    if "Positive" in sentiment: score += 3
    elif "Mixed" in sentiment:  score += 2
    elif "Neutral" in sentiment: score += 1

    # Reddit engagement volume (0–2)
    post_count = int(row.get("reddit_post_count", 0) or 0)
    if post_count >= 10: score += 2
    elif post_count >= 3: score += 1

    # Price volatility — high volatility = market opportunity (0–2)
    freq = str(row.get("price_change_freq", ""))
    if freq in ("Very frequent", "Frequent"): score += 2
    elif freq == "Moderate": score += 1

    # New / trending items (0–2)
    new_flag = str(row.get("new_or_upcoming", ""))
    if new_flag in ("New / upcoming", "Trending"): score += 2
    elif new_flag == "Potential new item": score += 1

    # Price competitiveness vs OCS (0–2)
    bbfyb = float(row.get("bbfyb_avg_price", 0) or 0)
    ocs   = float(row.get("ocs_avg_price", 0) or 0)
    if bbfyb > 0 and ocs > 0:
        if bbfyb <= ocs * 0.97:   score += 2   # BBFYB is cheaper → competitive edge
        elif bbfyb <= ocs * 1.02: score += 1   # roughly on par

    return score



# STRATEGIC ACTION

def strategic_action(score: int, ratio: float, new_flag: str,
                     velocity: str, sentiment: str) -> str:

    if score >= 14:
        return (
            "IMMEDIATE ACTION: Maximum stock allocation. "
            "Feature prominently in-store and online. "
            "Consider exclusive promotional bundle."
        )

    if score >= 11:
        return (
            "SCALE UP: Increase order volume by 20-30%. "
            "Negotiate better supplier terms. "
            "Highlight in weekly promotions."
        )

    if ratio < 0.25 and "New" in new_flag:
        return (
            "PILOT LAUNCH: Low market penetration but new/trending. "
            "Trial small batch, track 2-week sell-through before committing."
        )

    if score >= 8:
        return (
            "GROWTH OPPORTUNITY: Optimize shelf placement and pricing. "
            "A/B test promotional pricing vs competitors."
        )

    if "Negative" in sentiment:
        return (
            "REVIEW: Negative Reddit sentiment detected. "
            "Verify product quality, consider phasing out or renegotiating."
        )

    return (
        "MAINTAIN: Monitor pricing weekly. "
        "Replace if a higher-scoring alternative becomes available."
    )


# MAIN

def main():
    print("=== STEP 6: Executive Actionable Insights ===\n")

    df = pd.read_csv(SUMMARY_FILE)
    rows = []

    for _, row in df.iterrows():
        score  = priority_score(row)
        ratio  = float(row.get("presence_ratio", 0) or 0)
        action = strategic_action(
            score,
            ratio,
            str(row.get("new_or_upcoming", "")),
            str(row.get("sales_velocity", "")),
            str(row.get("reddit_sentiment", "")),
        )

        priority = (
            "HIGH"   if score >= 11
            else "MEDIUM" if score >= 7
            else "LOW"
        )

        rows.append({
            "insight_date":       datetime.utcnow().isoformat(),
            "product_name":       row.get("product_name", ""),
            "brand":              row.get("brand", ""),
            "market_penetration": ratio,
            "sales_velocity":     row.get("sales_velocity", ""),
            "sell_through_proxy": row.get("sell_through_proxy", ""),
            "price_change_freq":  row.get("price_change_freq", ""),
            "new_or_upcoming":    row.get("new_or_upcoming", ""),
            "reddit_sentiment":   row.get("reddit_sentiment", ""),
            "reddit_post_count":  row.get("reddit_post_count", 0),
            "bbfyb_avg_price":    row.get("bbfyb_avg_price", ""),
            "ocs_avg_price":      row.get("ocs_avg_price", ""),
            "priority_score":     score,
            "decision_priority":  priority,
            "strategic_action":   action,
        })

    out = (
        pd.DataFrame(rows)
        .sort_values("priority_score", ascending=False)
        .reset_index(drop=True)
    )

    out.to_csv(INSIGHTS_FILE, index=False)

    print(f"Saved {len(out)} rows -> {INSIGHTS_FILE}")

    print("\n=== TOP 10 STRATEGIC OPPORTUNITIES ===")
    for _, r in out.head(10).iterrows():
        print(f"\n[Score {r['priority_score']} | {r['decision_priority']}] {r['product_name']}")
        print(f"  Sentiment : {r['reddit_sentiment']}  ({r['reddit_post_count']} posts)")
        print(f"  Velocity  : {r['sales_velocity']}  |  Sell-through: {r['sell_through_proxy']}")
        print(f"  Action    : {r['strategic_action'][:80]}...")


if __name__ == "__main__":
    main()