import requests
from bs4 import BeautifulSoup
import json
import re

URL = "https://www.penzion-hoffer.sk/22413/obedove-menu"


def clean_price(text):
    """
    Vytiahne cenu ako NUMBER (float)
    """
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

    text = soup.get_text("\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    soup_text = ""
    meals = []

    for i, line in enumerate(lines):

        # polievka
        if "POLIEVKA" in line.upper():
            if i + 1 < len(lines):
                soup_text = clean_name(lines[i + 1])

        # ignoruj hlavičky
        if line.upper() in ["HLAVNÉ JEDLÁ", "DENNÉ MENU", "OBEDOVÉ MENU"]:
            continue

        price = clean_price(line)

        # jedlo (heuristika)
        if any(x in line for x in ["g", "Kurací", "steak", "omáč", "zemiak", "€"]):
            name = clean_name(line)

            if name and not price:
                meals.append({"name": name, "price": None})

            if price:
                if meals:
                    meals[-1]["price"] = price

    return {
        "restaurant": "Hoffer",
        "soup": soup_text,
        "meals": meals
    }


if __name__ == "__main__":
    print(json.dumps(scrape_hoffer(), indent=2, ensure_ascii=False))