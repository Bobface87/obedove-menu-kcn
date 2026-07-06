import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.penzion-hoffer.sk/22411/obedove-menu"


def extract_prices(text):
    match = re.search(r"\d+,\d+", text)
    if match:
        return float(match.group(0).replace(",", "."))
    return None


def scrape_hoffer():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")

    blocks = soup.find_all(["p", "div", "li"])

    meals = []
    soup_text = ""

    for b in blocks:
        text = b.get_text(" ", strip=True)

        if "POLIEVKA" in text.upper():
            soup_text = text

        price = extract_prices(text)

        if price:
            name = re.sub(r"\d+,\d+.*", "", text).strip()
            meals.append({
                "name": name,
                "price": price
            })

    return {
        "restaurant": "Hoffer",
        "soup": soup_text,
        "meals": meals[:6]
    }