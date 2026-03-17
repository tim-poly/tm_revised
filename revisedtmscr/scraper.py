import threading

from network import fetch_page
from parser import parse_products
from storage import append_to_csv
from utils import log
from config import BASE_URL
from bs4 import BeautifulSoup
from utils import brand_to_slug
import re
from parser import extract_country_map

sku_lock = threading.Lock()

def discover_brands():

    url = "https://www.thomann.se/cat_brands.html"

    print("Discovering brands...")

    html = fetch_page(url)

    if not html:
        print("Failed to load brand directory.")
        return []

    soup = BeautifulSoup(html, "html.parser")

    brands = set()

    for link in soup.find_all("a"):

        name = link.get_text(strip=True)

        if not name:
            continue

        slug = brand_to_slug(name)

        if not re.match("^[a-z]", slug):
            continue

        brands.add(slug)

    brands = sorted(brands)

    print(f"Discovered {len(brands)} brands")

    return brands

def scrape_all_pages(brand, global_skus):

    page = 1
    all_products = []

    while True:

        url = BASE_URL.format(brand, page)
        log(f"[SCRAPE] Brand: {brand} | Page: {page}")

        html = fetch_page(url)

        if html is None:
            if page == 1:
                print(f"Skipping brand {brand}")
                return []
            break

        products = parse_products(html)

        if not products:
            print(f"No products found for {brand} page {page}")
            break

        new_products = []

        for p in products:

            sku = p.get("sku")

            if not sku:
                continue

            with sku_lock:
                if sku in global_skus:
                    continue
                global_skus.add(sku)

                """""# --- NEW: build product URL (temporary slug method) ---
                name = p.get("name", "")
                slug = (
                    name.lower()
                    .replace(" ", "_")
                    .replace("-", "_")
                    .replace("/", "_")
                    .replace(".", "")
                )

                product_url = f"https://www.thomann.se/{slug}.htm"""

                product_url = p.get("url")
                product_html = fetch_page(product_url)

            if not product_html:
                continue

            # --- NEW: extract country map ---
            country_map = extract_country_map(product_html)

            # --- attach to product ---
            p["url_se"] = country_map.get("sv-SE")
            p["url_no"] = country_map.get("en-NO")
            p["url_dk"] = country_map.get("da-DK")
            p["url_fi"] = country_map.get("fi-FI")

            new_products.append(p)

        log(f"{brand} page {page} -> {len(new_products)} new products")

        all_products.extend(new_products)
        append_to_csv(new_products)
        page += 1

    return all_products