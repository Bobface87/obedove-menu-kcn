import json
import os
from hoffer import scrape_hoffer

OUTPUT_PATH = "docs/menu.json"


def build():
    print("🔄 Generujem menu...")

    data = []

    try:
        data.append(scrape_hoffer())
        print("✔ Hoffer OK")
    except Exception as e:
        print("❌ Hoffer error:", e)

    # sem budeme pridávať ďalšie reštaurácie
    # data.append(scrape_buganka())
    # data.append(scrape_quovadis())

    os.makedirs("docs", exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Hotovo -> docs/menu.json")


if __name__ == "__main__":
    build()