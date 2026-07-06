import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

URL = "https://www.penzion-hoffer.sk/22411/obedove-menu"

DAYS = {
    0: "PONDELOK",
    1: "UTOROK",
    2: "STREDA",
    3: "ŠTVRTOK",
    4: "PIATOK",
    5: "SOBOTA",
    6: "NEDEĽA"
}


def clean_price(text):
    match = re.search(r"\d+,\d+", text)
    if match:
        return float(match.group(0).replace(",", "."))
    return None


def clean_name(text):
    text = re.sub(r"^\d+g\t", "", text)
    text = re.sub(r"^\d+,\d+l\t", "", text)
    text = re.sub(r"\(\d+(,\d+)*\)", "", text)
    return text.strip()


def scrape_hoffer():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")

    today = DAYS[datetime.now().weekday()]

    text = soup.get_text("\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    soup_text = ""
    meals = []

    active = False

    for i, line in enumerate(lines):

        # 👉 zapni parsing iba pre dnešný deň
        if today in line.upper():
            active = True
            continue

        # 👉 keď narazíme na ďalší deň, stop
        if active and any(d in line.upper() for d in DAYS.values()) and today not in line.upper():
            break

        if not active:
            continue

        # polievka
        if "POLIEVKA" in line.upper():
            if i + 1 < len(lines):
                soup_text = clean_name(lines[i + 1])

        # ignoruj hlavičky
        if line.upper() in ["HLAVNÉ JEDLÁ", "OBEDOVÉ MENU"]:
            continue

        price = clean_price(line)

        if any(x in line for x in ["g", "Kurací", "steak", "omáč", "zemiak", "€"]):
            name = clean_name(line)

            if name and not price:
                meals.append({"name": name, "price": None})

            if price and meals:
                meals[-1]["price"] = price

    return {
        "restaurant": "Hoffer",
        "day": today,
        "soup": soup_text,
        "meals": meals
    }


if __name__ == "__main__":
    print(json.dumps(scrape_hoffer(), indent=2, ensure_ascii=False))
