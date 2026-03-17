import threading

from network import fetch_page
from parser import parse_products
from storage import append_to_csv
from utils import log
from config import BASE_URL
from bs4 import BeautifulSoup
from utils import brand_to_slug
import re
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

            new_products.append(p)

        log(f"{brand} page {page} -> {len(new_products)} new products")

        all_products.extend(new_products)
        append_to_csv(new_products)
        page += 1

    return all_products