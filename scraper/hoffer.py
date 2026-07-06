import requests
from bs4 import BeautifulSoup
import json
import re

URL = "https://www.penzion-hoffer.sk/22413/obedove-menu"


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

    # 🔥 KĽÚČOVÁ ZMENA:
    # berieme len hlavný obsah (nie celý web)
    content = soup.select_one("article, .content, .post, main")

    if not content:
        content = soup

    text = content.get_text("\n")

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    soup_text = ""
    meals = []

    for i, line in enumerate(lines):

        # polievka
        if "POLIEVKA" in line.upper():
            if i + 1 < len(lines):
                soup_text = clean_name(lines[i + 1])

        # ignorujeme zbytočné sekcie
        if line.upper() in [
            "HLAVNÉ JEDLÁ",
            "DENNÉ MENU",
            "OBEDOVÉ MENU",
            "PONDELOK",
            "UTOROK",
            "STREDA",
            "ŠTVRTOK",
            "PIATOK"
        ]:
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
        "soup": soup_text,
        "meals": meals[:6]  # 🔥 limit – iba obedové menu
    }


if __name__ == "__main__":
    print(json.dumps(scrape_hoffer(), indent=2, ensure_ascii=False))
