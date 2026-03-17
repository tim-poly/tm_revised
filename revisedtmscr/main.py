import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper import scrape_all_pages
from storage import save_to_csv
from utils import print_summary
from brands import TARGET_BRANDS
from config import MAX_WORKERS

# Thread safety
sku_lock = threading.Lock()
print_lock = threading.Lock()

def main():
    brands = TARGET_BRANDS

    if not brands:
        print("No brands found")
        return

    all_products = []
    global_skus = set()

    print("\nStarting parallel scraping...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = [
            executor.submit(scrape_all_pages, brand, global_skus)
            for brand in brands
        ]

        for future in as_completed(futures):
            result = future.result()
            all_products.extend(result)

    print_summary(all_products)
    save_to_csv(all_products)

if __name__ == "__main__":
    main()
