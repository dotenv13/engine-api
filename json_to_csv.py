import json
import csv

IN_FILE = "engines_mysakura.json"
ENGINES_CSV = "engines.csv"
IMAGES_CSV = "engine_images.csv"

ENGINE_FIELDS = [
    "product_id", "title", "make", "model", "year",
    "engine_code", "engine_type", "price", "currency",
    "stock_text", "oem", "description"
]

def main():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1) engines.csv
    with open(ENGINES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ENGINE_FIELDS)
        w.writeheader()

        seen = set()
        for item in data:
            pid = item.get("product_id")
            if not pid:
                continue
            if pid in seen:
                continue
            seen.add(pid)

            row = {k: item.get(k) for k in ENGINE_FIELDS}
            # защита: если вдруг price не int
            if row["price"] is not None and not isinstance(row["price"], int):
                try:
                    row["price"] = int(str(row["price"]).strip())
                except:
                    row["price"] = None

            w.writerow(row)

    # 2) engine_images.csv
    with open(IMAGES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "image_url", "sort_order"])

        for item in data:
            pid = item.get("product_id")
            if not pid:
                continue

            images = item.get("images") or []
            for idx, url in enumerate(images):
                w.writerow([pid, url, idx])

    print("OK: создано", ENGINES_CSV, "и", IMAGES_CSV)

if __name__ == "__main__":
    main()
