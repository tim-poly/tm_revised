import json
from bs4 import BeautifulSoup
from utils import BRAND_SLUG_MAP
def extract_items_json(html):

    start = html.find('"items":')

    if start == -1:
        return None

    start = html.find('[', start)

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(html)):

        char = html[i]

        if char == '"' and not escape:
            in_string = not in_string

        if char == "\\" and not escape:
            escape = True
            continue

        escape = False

        if not in_string:

            if char == '[':
                depth += 1

            elif char == ']':
                depth -= 1

                if depth == 0:
                    return html[start:i+1]

    return None


def slugify(name):
    return (
        name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace(".", "")
    )


def parse_products(html):

    items_json = extract_items_json(html)

    if not items_json:
        print("Could not find items array")
        return []

    items = json.loads(items_json)

    products = []

    """for item in items:
        slug = slugify(item.get("item_name", ""))
        url = f"https://www.thomann.se/{slug}.htm"
        product = {
            "sku": item.get("item_id"),
            "name": item.get("item_name"),
            "brand": item.get("item_brand"),
            "price": item.get("price"),
            "currency": item.get("currency"),
            "category": item.get("item_category"),
            "url": url,
        }

        products.append(product)"""
    for item in items:

        brand = item.get("item_brand", "")
        name = item.get("item_name", "")

        if not brand or not name:
            continue

        brand_slug = BRAND_SLUG_MAP.get(brand, slugify(brand))
        name_slug = slugify(name)

        if name_slug.startswith(brand_slug):
            slug = name_slug
        else:
            slug = f"{brand_slug}_{name_slug}"


        url = f"https://www.thomann.se/{slug}.htm"

        product = {
            "sku": item.get("item_id"),
            "name": name,
            "brand": brand,
            "price": item.get("price"),
            "currency": item.get("currency"),
            "category": item.get("item_category"),
            "url": url,
        }

        products.append(product)
    return products

def extract_country_map(html):

    soup = BeautifulSoup(html, "html.parser")

    country_map = {}

    for link in soup.select("link[rel='alternate']"):

        hreflang = link.get("hreflang")
        href = link.get("href")

        if not hreflang or not href:
            continue

        country_map[hreflang] = href

    return country_map