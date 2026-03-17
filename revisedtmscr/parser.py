import json

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


def parse_products(html):

    items_json = extract_items_json(html)

    if not items_json:
        print("Could not find items array")
        return []

    items = json.loads(items_json)

    products = []

    for item in items:

        product = {
            "sku": item.get("item_id"),
            "name": item.get("item_name"),
            "brand": item.get("item_brand"),
            "price": item.get("price"),
            "currency": item.get("currency"),
            "category": item.get("item_category"),
            "url": f"https://www.thomann.se/{item.get('item_id')}.htm"
        }

        products.append(product)

    return products