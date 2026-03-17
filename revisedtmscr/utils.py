from datetime import datetime
import threading

##terminal log##
def log(message):
    now = datetime.now().strftime("%H:%M:%S")
    thread = threading.current_thread().name
    print(f"[{now}] [{thread}] {message}")

##brand to slug##
def brand_to_slug(name):

    slug = name.lower()

    slug = slug.replace("&", "and")
    slug = slug.replace(" ", "_")
    slug = slug.replace(".", "")
    slug = slug.replace("-", "_")

    return slug
##print summary##
def print_summary(products):

    print("\n--- SCRAPE SUMMARY ---")
    print("Total products:", len(products))

    prices = [float(p["price"]) for p in products if p["price"]]

    if prices:
        print("Min price:", min(prices))
        print("Max price:", max(prices))
        print("Average price:", round(sum(prices) / len(prices), 2))