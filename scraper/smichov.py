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



def scrape_smichov():

    print(
        "Načítavam Smíchov..."
    )


    soup = download_page()


    image_url = None


    for img in soup.find_all("img"):

        src = img.get("src")

        if not src:
            continue


        if "Obedove" in src or "obedove" in src:

            image_url = src
            break



    if not image_url:

        raise Exception(
            "Obrázok menu Smíchov sa nenašiel"
        )



    if image_url.startswith("/"):

        image_url = (
            "https://www.restauraciasmichov.sk"
            + image_url
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