import requests
from bs4 import BeautifulSoup

from ocr import extract_text_from_image
from buganka_ocr_parser import parse_buganka_menu


URL = "https://www.buganka.sk/obedove-menu"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/137 Safari/537.36"
    )
}



def get_image_url():

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


    for img in soup.find_all("img"):

        src = img.get(
            "src",
            ""
        )


        if (
            "buganka" in src.lower()
            and "logo" not in src.lower()
        ):

            return src


    return None



def scrape_buganka():

    print(
        "Načítavam Buganku..."
    )


    image_url = get_image_url()


    if not image_url:

        raise Exception(
            "Obrázok Buganky sa nenašiel"
        )



    try:

        print(
            "Spúšťam Buganka OCR..."
        )


        text = extract_text_from_image(
            image_url
        )


        if not text:

            raise Exception(
                "OCR vrátil prázdny text"
            )



        result = parse_buganka_menu(
            text
        )



        if not result:

            raise Exception(
                "Parser vrátil prázdny výsledok"
            )



        # ochrana - OCR musí nájsť aspoň nejaké jedlá

        if (
            not result.get("soup", {}).get("items")
            and
            not result.get("meals", {}).get("items")
        ):

            raise Exception(
                "OCR nenašlo menu položky"
            )


        result["restaurant"] = "Buganka"

        result["type"] = "ocr_menu"


        return result



    except Exception as e:


        print(
            "⚠️ Buganka OCR zlyhalo:",
            e
        )


        print(
            "Používam iba obrázok menu"
        )


        return {

            "restaurant": "Buganka",

            "type": "image_menu",

            "image_url": image_url,

            "soup": "",

            "meals": []

        }



if __name__ == "__main__":


    import json


    result = scrape_buganka()


    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )