import json
import os

from hoffer import scrape_hoffer
from quovadis import scrape_quovadis

OUTPUT_PATH = "docs/menu.json"


def build():
    print("🔄 Generujem menu...")

    data = []

    # Hoffer
    try:
        data.append(scrape_hoffer())
        print("✔ Hoffer OK")
    except Exception as e:
        print("❌ Hoffer error:", e)

    # Quo Vadis (link mode)
    try:
        data.append(scrape_quovadis())
        print("✔ Quo Vadis OK")
    except Exception as e:
        print("❌ Quo Vadis error:", e)

    # vytvor docs priečinok ak neexistuje
    os.makedirs("docs", exist_ok=True)

    # zapis JSON
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ HOTOVO -> docs/menu.json")


if __name__ == "__main__":
    build()