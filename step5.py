"""
Reddit sentiment + business analytics.

"""

import re
import time
import random
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

# PATHS

OUTPUT_DIR    = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
PRODUCTS_FILE = OUTPUT_DIR / "products_pricing_snapshot.csv"
MARKET_FILE   = OUTPUT_DIR / "market_comparison.csv"
REDDIT_CACHE  = OUTPUT_DIR / "reddit_sentiment_raw.csv"
SUMMARY_FILE  = OUTPUT_DIR / "business_analytics_summary.csv"


# REDDIT CONFIG — minimal, safe

REDDIT_HEADERS = {
    "User-Agent": "cannabis-retail-research/1.0 (Ontario market study; contact: research@example.com)"
}
# Single subreddit per run — rotate if needed
SUBREDDIT      = "OntarioCannabis"
REDDIT_TIMEOUT = 25
BASE_DELAY     = 4.0      # seconds between requests
MAX_RETRIES    = 2
MAX_WAIT       = 60       # max backoff seconds



# NORMALIZE

def normalize(name: str) -> str:
    text = re.sub(r"[^a-z0-9 ]", " ", str(name).lower().strip())
    text = re.sub(r"\b\d+(\.\d+)?\s?(g|mg|ml|pack|x)\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_brand(product_name: str) -> str:
    """
    Try to get a short brand key from product name.
    Uses first 1-2 meaningful words.
    """
    stop = {"the","and","for","with","by","in","of","pre","roll","infused",
            "live","resin","rosin","flower","oil","cart","510","thc","cbd"}
    words = [w for w in normalize(product_name).split() if w not in stop and len(w) > 2]
    return words[0] if words else normalize(product_name)[:12]



# REDDIT FETCH with backoff

def reddit_search(term: str, limit: int = 15) -> list:
    url    = f"https://www.reddit.com/r/{SUBREDDIT}/search.json"
    params = {"q": term, "limit": limit, "sort": "relevance",
              "t": "year", "restrict_sr": 1}

    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.get(url, params=params,
                             headers=REDDIT_HEADERS, timeout=REDDIT_TIMEOUT)

            if r.status_code == 429:
                wait = min(BASE_DELAY * (3 ** attempt) + random.uniform(1, 3), MAX_WAIT)
                print(f"    429 rate-limit — sleeping {wait:.0f}s")
                time.sleep(wait)
                continue

            if r.status_code == 404:
                return []   # subreddit gone/banned — skip silently

            r.raise_for_status()
            return [c["data"] for c in r.json()["data"]["children"]]

        except requests.exceptions.Timeout:
            print(f"    Timeout on attempt {attempt+1}")
            time.sleep(BASE_DELAY * 2)

        except Exception as e:
            print(f"    Reddit error: {e}")
            break

    return []



# SCORE SENTIMENT

POS = {"love","great","amazing","best","good","nice","smooth","recommend",
       "excellent","fire","top","favourite","favorite","potent","clean",
       "worth","enjoyed","solid","impressive","tasty","strong"}
NEG = {"bad","terrible","awful","worst","hate","avoid","dry","harsh",
       "overpriced","expensive","weak","disappointing","meh","skip",
       "waste","garbage","poor","stale","burnt","chemical"}


def score_posts(posts: list) -> dict:
    if not posts:
        return {"sentiment_label": "No data", "post_count": 0,
                "positive_signals": 0, "negative_signals": 0,
                "avg_upvotes": 0, "top_comment": ""}

    pos = neg = 0
    upvotes   = []
    best_score, top_comment = -9999, ""

    for p in posts:
        text = (str(p.get("title","")) + " " + str(p.get("selftext",""))).lower()
        pos += sum(1 for w in POS if w in text)
        neg += sum(1 for w in NEG if w in text)
        upvotes.append(p.get("score", 0))
        if p.get("score", 0) > best_score:
            best_score  = p.get("score", 0)
            top_comment = p.get("title", "")[:120]

    if pos > neg * 1.5:   label = "Positive"
    elif neg > pos * 1.5: label = "Negative"
    elif pos > 0 or neg > 0: label = "Mixed"
    else:                  label = "Neutral"

    return {
        "sentiment_label":   label,
        "post_count":        len(posts),
        "positive_signals":  pos,
        "negative_signals":  neg,
        "avg_upvotes":       round(sum(upvotes) / len(upvotes), 1),
        "top_comment":       top_comment,
    }



# LOAD EXISTING CACHE

def load_cache() -> dict:
    """Returns dict: brand_key -> sentiment_dict"""
    if not REDDIT_CACHE.exists():
        return {}
    df = pd.read_csv(REDDIT_CACHE)
    cache = {}
    for _, row in df.iterrows():
        key = str(row.get("brand_key", ""))
        if key:
            cache[key] = row.to_dict()
    print(f"Loaded {len(cache)} cached brand entries")
    return cache


def save_cache(cache: dict):
    rows = list(cache.values())
    pd.DataFrame(rows).to_csv(REDDIT_CACHE, index=False)



# ANALYTICS HELPERS

def sales_velocity(store_count: int, sentiment: str) -> str:
    s = (3 if store_count >= 8 else 2 if store_count >= 4 else 1)
    s += (3 if "Positive" in sentiment else 2 if "Mixed" in sentiment else 1)
    return "High" if s >= 5 else "Medium" if s >= 3 else "Low"


def price_change_freq(bbfyb, hibuddy, ocs) -> str:
    vals = set()
    for p in [bbfyb, hibuddy, ocs]:
        try: vals.add(round(float(p), 0))
        except Exception: pass
    n = len(vals)
    return "Very frequent" if n >= 3 else "Moderate" if n == 2 else "Stable"


def sell_through(ratio: float, sentiment: str) -> str:
    s = (3 if ratio >= 0.7 else 2 if ratio >= 0.4 else 1)
    s += (3 if "Positive" in sentiment else 2 if "Mixed" in sentiment else 1)
    return "High" if s >= 5 else "Medium" if s >= 3 else "Low"


NEW_KW = ["new","limited","launch","exclusive","fresh","drop","lto"]
def new_or_upcoming(name: str, store_count: int, sentiment: str) -> str:
    nl = str(name).lower()
    if any(k in nl for k in NEW_KW): return "New / upcoming"
    if store_count <= 2:             return "Potential new item"
    if "Positive" in sentiment:      return "Trending"
    return "Existing product"



# MAIN

def main():
    print("=== STEP 5: Reddit Sentiment + Business Analytics ===\n")
    print(f"Subreddit: r/{SUBREDDIT}\n")

    # ---- load data ----
    products_df = pd.read_csv(PRODUCTS_FILE) if PRODUCTS_FILE.exists() else pd.DataFrame()
    market_df   = pd.read_csv(MARKET_FILE)   if MARKET_FILE.exists()   else pd.DataFrame()

    if products_df.empty:
        print("WARNING: products_pricing_snapshot.csv not found or empty")
        print("Building summary from market_comparison.csv only")
        merged = market_df.copy()
    else:
        products_df = products_df.drop_duplicates(subset=["store_name","product_name"])
        market_df   = market_df.drop_duplicates(subset=["store_name","product_name"]) if not market_df.empty else market_df

        if market_df.empty:
            merged = products_df.copy()
        else:
            merged = pd.merge(products_df, market_df,
                              on=["store_name","product_name"],
                              how="left", suffixes=("","_mkt"))

    merged["product_key"] = merged["product_name"].apply(normalize)

    # aggregate per unique product
    agg_cols = {"product_name": "first", "store_name": "nunique"}
    for col in ["brand","bbfyb_regular","hibuddy_price","ocs_price",
                "bbfyb_price","regular_price"]:
        if col in merged.columns:
            agg_cols[col] = "first"

    agg = (merged.groupby("product_key")
                 .agg(agg_cols)
                 .reset_index(drop=True))

    agg.rename(columns={"store_name": "store_count"}, inplace=True)

    # resolve price columns
    if "bbfyb_price" not in agg.columns and "bbfyb_regular" in agg.columns:
        agg["bbfyb_price"] = agg["bbfyb_regular"]
    elif "bbfyb_price" not in agg.columns and "regular_price" in agg.columns:
        agg["bbfyb_price"] = agg["regular_price"]

    for col in ["bbfyb_price","hibuddy_price","ocs_price"]:
        if col not in agg.columns:
            agg[col] = None

    total_stores = max(int(merged["store_name"].nunique()), 1)

    # ---- build brand list — DEDUPLICATED ----
    agg["brand_key"] = agg.apply(
        lambda r: normalize(str(r.get("brand","")) or extract_brand(r["product_name"])),
        axis=1
    )

    unique_brands = agg["brand_key"].dropna().unique().tolist()
    unique_brands = [b for b in unique_brands if b]

    print(f"Unique products  : {len(agg)}")
    print(f"Unique brand keys: {len(unique_brands)}")
    print(f"(Reddit will search once per brand, not per product)\n")

    # ---- load cache ----
    cache = load_cache()
    new_fetches = 0
    todo = [b for b in unique_brands if b not in cache]

    print(f"Brands to fetch : {len(todo)}")
    print(f"Already cached  : {len(unique_brands) - len(todo)}\n")

    if todo:
        print(f"Fetching Reddit sentiment (r/{SUBREDDIT})...\n")

    for i, brand_key in enumerate(todo):
        print(f"  [{i+1}/{len(todo)}] {brand_key}")
        posts  = reddit_search(brand_key, limit=15)
        result = score_posts(posts)
        result["brand_key"] = brand_key
        cache[brand_key]    = result
        new_fetches += 1

        # save cache every 10 fetches so progress isn't lost on crash
        if new_fetches % 10 == 0:
            save_cache(cache)
            print(f"    (cache saved — {new_fetches} new entries)")

        # polite delay: longer after 429s, jitter to avoid patterns
        delay = BASE_DELAY + random.uniform(0.5, 1.5)
        time.sleep(delay)

    save_cache(cache)
    print(f"\nReddit cache saved -> {REDDIT_CACHE}")
    print(f"New fetches this run: {new_fetches}")

    # ---- build analytics summary ----
    print("\nBuilding business analytics summary...")
    rows = []

    for _, row in agg.iterrows():
        brand_key = row.get("brand_key", "")
        sentiment = cache.get(brand_key, {})
        label     = sentiment.get("sentiment_label", "No data")
        stores    = int(row.get("store_count", 0) or 0)
        ratio     = round(stores / total_stores, 2)

        rows.append({
            "analysis_date":        datetime.utcnow().isoformat(),
            "product_name":         row["product_name"],
            "brand":                row.get("brand", ""),
            "carried_by_stores":    stores,
            "total_stores_sampled": total_stores,
            "presence_ratio":       ratio,
            "bbfyb_avg_price":      row.get("bbfyb_price", ""),
            "hibuddy_avg_price":    row.get("hibuddy_price", ""),
            "ocs_avg_price":        row.get("ocs_price", ""),
            "sales_velocity":       sales_velocity(stores, label),
            "sell_through_proxy":   sell_through(ratio, label),
            "price_change_freq":    price_change_freq(
                                        row.get("bbfyb_price"),
                                        row.get("hibuddy_price"),
                                        row.get("ocs_price")),
            "new_or_upcoming":      new_or_upcoming(row["product_name"], stores, label),
            "reddit_sentiment":     label,
            "reddit_post_count":    sentiment.get("post_count", 0),
            "reddit_pos_signals":   sentiment.get("positive_signals", 0),
            "reddit_neg_signals":   sentiment.get("negative_signals", 0),
            "reddit_avg_upvotes":   sentiment.get("avg_upvotes", 0),
            "reddit_top_comment":   sentiment.get("top_comment", ""),
        })

    out = (pd.DataFrame(rows)
             .sort_values("presence_ratio", ascending=False)
             .reset_index(drop=True))

    out.to_csv(SUMMARY_FILE, index=False)
    print(f"Saved {len(out)} rows -> {SUMMARY_FILE}")

    print("\nTop 5 by presence ratio:")
    cols = ["product_name","presence_ratio","reddit_sentiment","sales_velocity"]
    print(out[[c for c in cols if c in out.columns]].head().to_string(index=False))


if __name__ == "__main__":
    main()