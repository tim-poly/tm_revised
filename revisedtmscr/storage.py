import csv
import threading

progress_lock = threading.Lock()
csv_lock = threading.Lock()

products_written = 0
written_skus = set()

def append_to_csv(products):

    global products_written

    if not products:
        return

    keys = products[0].keys()

    with csv_lock:

        file_exists = False

        try:
            with open("revised_tm_list.csv"):
                file_exists = True
        except:
            pass

        with open("revised_tm_list.csv", "a", newline="", encoding="utf-8-sig") as f:

            writer = csv.DictWriter(f, fieldnames=keys)

            if not file_exists:
                writer.writeheader()

            for product in products:

                sku = product["sku"]

                if sku in written_skus:
                    continue

                written_skus.add(sku)

                writer.writerow(product)

                with progress_lock:
                    products_written += 1
                    print(f"[PROGRESS] {products_written} products saved")


def save_to_csv(products):

    if not products:
        print("No products to save")
        return

    keys = products[0].keys()

    with open("revised_tm_list_update.csv", "w", newline="", encoding="utf-8-sig") as f:

        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(products)

    print(f"Saved {len(products)} products to test_improved_list.csv")