"""
step3.py — Scrape product listings from bestbangforyourbud.com
for stores in Burlington / surrounding cities.
"""

import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pathlib import Path


# CONFIG

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

BBFYB_CITIES = [
    "Burlington",
    "Hamilton",
    "Oakville",
    "Mississauga",
    "Milton",
    "Brampton",
    "Stoney-Creek",
]

BASE_URL   = "https://bestbangforyourbud.com"
CITY_URL   = BASE_URL + "/en/stores/ON/{city}"
TIMEOUT    = 30
DELAY      = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

PRICE_RE = re.compile(r"\$\s*\d+(?:\.\d{2})?")
PROMO_RE = re.compile(
    r"(sale|promo|deal|special|offer|limited|ends?|until|expires?|off\b)",
    re.IGNORECASE,
)



# HELPERS

def get_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()



# LIST STORE URLS FOR A CITY

def get_store_urls(city: str) -> list[dict]:
    url  = CITY_URL.format(city=city)
    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")

    stores = []
    for a in soup.select("a.stores-card, a[href*='/en/stores/']"):
        href = a.get("href", "")
        if "/en/stores/" not in href:
            continue
        parts = href.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        slug = parts[-1]
        full_url = BASE_URL + href if href.startswith("/") else href
        # derive store name from card heading
        name_el = a.select_one("h2, h3, .store-name, .card-title")
        name = clean(name_el.get_text()) if name_el else slug.replace("-", " ").title()
        stores.append({"city": city, "store_name": name, "store_url": full_url})

    return stores



# SCRAPE PRODUCTS FROM ONE STORE

def scrape_products(store: dict) -> list[dict]:
    html = get_html(store["store_url"])
    soup = BeautifulSoup(html, "lxml")
    products = []

    for card in soup.select(
        "div.product-card, div[class*='product'], article[class*='product']"
    ):
        # --- name ---
        name_el = card.select_one(
            ".product-card-name, .product-name, h3, h2, [class*='name']"
        )
        if not name_el:
            continue

        name_lines = [
            l.strip()
            for l in name_el.get_text("\n", strip=True).split("\n")
            if l.strip()
        ]
        product_name = name_lines[0] if name_lines else ""
        size_format  = name_lines[1] if len(name_lines) > 1 else ""

        if not product_name:
            continue

        # --- brand ---
        brand_el = card.select_one(
            ".product-card-brand, .brand, [class*='brand']"
        )
        brand = clean(brand_el.get_text()) if brand_el else ""

        # --- price ---
        price_el = card.select_one(
            ".product-card-price, .price, [class*='price']"
        )
        price_text = clean(price_el.get_text()) if price_el else ""
        prices = PRICE_RE.findall(price_text)

        regular_price = ""
        sale_price    = ""
        if len(prices) == 1:
            regular_price = prices[0]
        elif len(prices) >= 2:
            # assume higher = regular, lower = sale
            vals = sorted(
                [float(p.replace("$", "").strip()) for p in prices]
            )
            regular_price = f"${vals[-1]:.2f}"
            sale_price    = f"${vals[0]:.2f}"

        # --- promo duration ---
        promo_duration = "Not listed"
        full_text = card.get_text(" ", strip=True)
        if PROMO_RE.search(full_text):
            # look for date-like pattern near promo words
            date_m = re.search(
                r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
                r"[\w\s,]*\d{1,2}",
                full_text,
                re.IGNORECASE,
            )
            if date_m:
                promo_duration = date_m.group().strip()
            else:
                promo_duration = "On sale (end date not listed)"

        products.append({
            "store_name":        store["store_name"],
            "store_city":        store["city"],
            "product_name":      product_name,
            "brand":             brand,
            "size_format":       size_format,
            "regular_price":     regular_price,
            "sale_price":        sale_price,
            "promotion_duration": promo_duration,
            "source_url":        store["store_url"],
        })

    return products



# MAIN

def main():
    all_stores   = []
    all_products = []

    for city in BBFYB_CITIES:
        print(f"\n--- City: {city} ---")
        try:
            stores = get_store_urls(city)
            print(f"  Found {len(stores)} store(s)")
        except Exception as e:
            print(f"  City page failed: {e}")
            continue

        for store in stores:
            print(f"  Scraping: {store['store_name']}")
            all_stores.append(store)
            try:
                products = scrape_products(store)
                all_products.extend(products)
                print(f"    {len(products)} products")
            except Exception as e:
                print(f"    Failed: {e}")
            time.sleep(DELAY)

    # save products
    df = pd.DataFrame(all_products)
    if df.empty:
        print("\nNo products scraped — check if BBFYB site structure changed.")
    else:
        out = OUTPUT_DIR / "products_pricing_snapshot.csv"
        df.to_csv(out, index=False)
        print(f"\nSaved {len(df)} product rows -> {out}")

    # save store list (useful cross-reference)
    stores_df = pd.DataFrame(all_stores).drop_duplicates(subset=["store_url"])
    stores_df.to_csv(OUTPUT_DIR / "bbfyb_stores.csv", index=False)
    print(f"Saved {len(stores_df)} BBFYB stores -> output/bbfyb_stores.csv")


if __name__ == "__main__":
    main()