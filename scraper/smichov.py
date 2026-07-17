import re

import requests
from bs4 import BeautifulSoup


URL = "https://www.restauraciasmichov.sk/obedove-menu"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137 Safari/537.36"
    )
}


BASE_URL = "https://www.restauraciasmichov.sk"


def download_page():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


def normalize_url(url):

    if not url:
        return None

    url = url.strip()

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("/"):
        return BASE_URL + url

    return url


def looks_like_menu(url):

    if not url:
        return False

    text = url.lower()

    return (
        "obedove" in text
        or "obedov" in text
        or "menu" in text
    )


def find_image(soup):

    #
    # 1. klasické IMG
    #
    for img in soup.find_all("img"):

        for attr in (
            "src",
            "data-src",
            "data-lazy-src",
            "data-original",
            "srcset"
        ):

            value = img.get(attr)

            if not value:
                continue

            # srcset obsahuje viac obrázkov
            if attr == "srcset":
                value = value.split(",")[0].strip().split(" ")[0]

            if looks_like_menu(value):

                return normalize_url(value)

    #
    # 2. background-image
    #
    html = str(soup)

    match = re.search(
        r'background-image\s*:\s*url\((.*?)\)',
        html,
        re.IGNORECASE
    )

    if match:

        url = (
            match.group(1)
            .strip("'\" ")
        )

        if looks_like_menu(url):

            return normalize_url(url)

    #
    # 3. posledná záchrana - regex cez celé HTML
    #
    match = re.search(
        r'(/images/[^"\']*?(?:obedove|menu)[^"\']*\.(?:jpg|jpeg|png|webp))',
        html,
        re.IGNORECASE
    )

    if match:

        return normalize_url(
            match.group(1)
        )

    #
    # 4. absolútna URL kdekoľvek v HTML
    #
    match = re.search(
        r'(https?://[^"\']*?(?:obedove|menu)[^"\']*\.(?:jpg|jpeg|png|webp))',
        html,
        re.IGNORECASE
    )

    if match:

        return match.group(1)

    return None


def scrape_smichov():

    print(
        "Načítavam Smíchov..."
    )

    soup = download_page()

    image_url = find_image(
        soup
    )

    if not image_url:

        raise Exception(
            "Obrázok menu Smíchov sa nenašiel"
        )

    return {
        "restaurant": "Smíchov",
        "type": "image_menu",
        "image_url": image_url,
        "soup": "",
        "meals": []
    }


if __name__ == "__main__":

    import json

    result = scrape_smichov()

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )