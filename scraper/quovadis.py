import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.quovadisnitra.sk/tyzdenne-menu/"


def scrape_quovadis():

    print("Načítavam Quo Vadis...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0 Safari/537.36"
        ),
        "Referer": "https://www.google.com/",
        "Accept-Language": "sk-SK,sk;q=0.9,en;q=0.8",
    }

    res = requests.get(
        URL,
        headers=headers,
        timeout=20,
    )

    print("HTTP STATUS:", res.status_code)

    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    images = []

    for img in soup.find_all("img"):

        src = img.get("src")

        if not src:
            continue

        if "/2026/" not in src:
            continue

        if "724x1024" not in src:
            continue

        images.append(src)

    # odstránenie duplicít pri zachovaní poradia
    images = list(dict.fromkeys(images))

    print("\n===== QUO VADIS OBRÁZZKY =====")
    for img in images:
        print(img)
    print("===== KONIEC OBRÁZKOV =====\n")

    # Pondelok=0 ... Piatok=4
    weekday = datetime.today().weekday()

    image_url = ""

    if 0 <= weekday <= 4 and len(images) > weekday:
        image_url = images[weekday]

    return {
        "restaurant": "Quo Vadis",
        "type": "image_menu",
        "image_url": image_url,
        "soup": "",
        "meals": []
    }