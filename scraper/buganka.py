import requests
from bs4 import BeautifulSoup


URL = "https://www.buganka.sk/obedove-menu"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137 Safari/537.36"
    )
}


def scrape_buganka():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    image_url = ""

    for img in soup.find_all("img"):

        src = img.get("src", "")

        if (
            "buganka" in src.lower()
            and "logo" not in src.lower()
        ):
            image_url = src
            break

    if not image_url:
        raise Exception("Obrázok týždenného menu sa nenašiel")

    return {
        "restaurant": "Buganka",
        "type": "image_menu",
        "image_url": image_url,
        "soup": "",
        "meals": []
    }


if __name__ == "__main__":

    result = scrape_buganka()
    print(result["image_url"])