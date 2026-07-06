import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.quovadisnitra.sk/tyzdenne-menu/"


def scrape_quovadis():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")

    meals = []

    # vytiahni textové bloky
    items = soup.find_all(["p", "li", "td"])

    for item in items:
        text = item.get_text(" ", strip=True)

        # cena
        match = re.search(r"\d+,\d+", text)
        price = float(match.group(0).replace(",", ".")) if match else None

        # jedlo (heuristika)
        if price:
            name = re.sub(r"\d+,\d+.*", "", text).strip()
            meals.append({
                "name": name,
                "price": price
            })

    return {
        "restaurant": "Quo Vadis",
        "soup": "",
        "meals": meals[:6]
    }