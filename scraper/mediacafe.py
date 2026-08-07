import requests
from bs4 import BeautifulSoup


URL = "https://www.mediacafe.sk/obedove-menu/"


def scrape_mediacafe():

    print("Načítavam Media Cafe...")


    r = requests.get(
        URL,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    r.raise_for_status()


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    images = []


    for img in soup.find_all(
        "img",
        src=True
    ):

        src = img["src"]


        if "obedove_menu" in src.lower():

            if src.startswith("//"):

                src = "https:" + src


            elif src.startswith("/"):

                src = (
                    "https://www.mediacafe.sk"
                    +
                    src
                )


            images.append(src)



    if not images:

        raise Exception(
            "Obrázok obedového menu Media Cafe sa nenašiel"
        )


    image_url = images[0]


    print(
        "Nájdený obrázok:",
        image_url
    )


    return {

        "restaurant": "Media Cafe",

        "type": "image_menu",

        "image_url": image_url,

        "soup": None,

        "meals": []

    }



def main():

    import json


    data = scrape_mediacafe()


    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )



if __name__ == "__main__":

    main()