import json
from hoffer import scrape_hoffer

OUTPUT = "docs/menu.json"


def build():
    data = []

    print("Scraping Hoffer...")
    data.append(scrape_hoffer())

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("DONE -> menu.json")


if __name__ == "__main__":
    build()