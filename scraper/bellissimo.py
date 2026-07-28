import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL = "https://bellissimonitra.com/obedove-menu/"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137 Safari/537.36"
    )
}



def find_image_url(soup):

    """
    Nájde aktuálne Bellissimo menu.
    """

    possible_urls = []


    for img in soup.find_all("img"):

        sources = [

            img.get("src", ""),

            img.get("data-src", ""),

            img.get("data-lazy-src", ""),

        ]


        srcset = img.get(
            "srcset",
            ""
        )


        if srcset:

            sources.extend(
                [
                    x.strip().split(" ")[0]
                    for x in srcset.split(",")
                ]
            )


        for src in sources:

            if not src:
                continue


            src_lower = src.lower()


            if (
                "menu" in src_lower
                and
                (
                    "bell" in src_lower
                    or
                    "obed" in src_lower
                )
            ):

                possible_urls.append(src)



    if not possible_urls:

        return None



    # prvý nájdený obrázok

    return urljoin(
        URL,
        possible_urls[0]
    )




def scrape_bellissimo():


    print(
        "Načítavam Bellissimo..."
    )


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



    image_url = find_image_url(
        soup
    )



    if not image_url:

        raise Exception(
            "Obrázok menu Bellissimo sa nenašiel"
        )



    print(
        "Bellissimo obrázok:",
        image_url
    )



    return {

        "restaurant": "Bellissimo",

        "type": "image_menu",

        "image_url": image_url,

        "soup": "",

        "meals": []

    }