import threading

from network import fetch_page
from parser import parse_products
from storage import append_to_csv
from utils import log
from config import BASE_URL, FETCH_ALTERNATE_URLS
from bs4 import BeautifulSoup
from utils import brand_to_slug
import re
from parser import extract_country_map

resolved_urls = {}

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
            name = p.get("name", "") or ""
            item_brand = p.get("brand", "") or ""

            if not sku:
                continue

            with sku_lock:
                if sku in global_skus:
                    continue
                global_skus.add(sku)

            product_url = resolved_urls.get(sku) or p.get("url")
            if not product_url:
                continue

            # If your only requirement is the Swedish product URL, don't hit the product page at all.
            p["url_se"] = product_url
            if not FETCH_ALTERNATE_URLS:
                new_products.append(p)
                continue

            product_html, status = fetch_page(product_url, return_status=True)

            # Try different URL variants only when we got a real 404 (bad slug), not when we are blocked (403).
            if not product_html and status == 404 and name:
                name_slug = (
                    name.lower()
                    .replace(" ", "_")
                    .replace("-", "_")
                    .replace("/", "_")
                    .replace(".", "")
                )

                candidates = [f"https://www.thomann.se/{name_slug}.htm"]

                if item_brand:
                    raw_brand_slug = (
                        item_brand.lower()
                        .replace(" ", "_")
                        .replace("-", "_")
                        .replace(".", "")
                    )
                    candidates.append(f"https://www.thomann.se/{raw_brand_slug}_{name_slug}.htm")

                for candidate_url in candidates:
                    candidate_html, candidate_status = fetch_page(candidate_url, return_status=True)
                    if candidate_html:
                        product_url = candidate_url
                        product_html = candidate_html
                        status = candidate_status
                        break

            # If still nothing → skip
            if not product_html:
                print(f"FAILED to fetch product page (status={status}) for {product_url}")
                continue

            # ✅ SUCCESS → store correct URL
            p["url"] = product_url

            # ✅ CACHE IT (important!)
            resolved_urls[sku] = product_url
            print(f"FINAL URL USED: {product_url}")
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
