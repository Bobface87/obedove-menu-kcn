import re
import time
import random

import requests
from bs4 import BeautifulSoup

from smichov_ocr_parser import parse_smichov_menu
from ocr import extract_text_from_image


URL = "https://www.restauraciasmichov.sk/obedove-menu"

BASE_URL = "https://www.restauraciasmichov.sk"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/150 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Encoding": (
        "gzip, deflate, br"
    ),
    "Accept-Language": (
        "sk-SK,sk;q=0.9,en;q=0.8"
    ),
}



def download_page():

    url = (
        URL
        + f"?nocache={random.randint(1000,999999)}"
    )


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()


    print(
        "Content-Type:",
        response.headers.get(
            "Content-Type"
        )
    )


    print(
        "Content-Encoding:",
        response.headers.get(
            "Content-Encoding"
        )
    )


    print(
        "Veľkosť odpovede:",
        len(response.content),
        "bytes"
    )


    if len(response.content) < 15000:

        raise Exception(
            "Smíchov vrátil krátku odpoveď"
        )



    html = response.text


    clean = html.lstrip().lower()



    if (
        "<html" not in clean
        and "<!doctype" not in clean
    ):

        raise Exception(
            "Smíchov vrátil neplatné HTML"
        )



    return BeautifulSoup(
        html,
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



            if attr == "srcset":

                value = (
                    value
                    .split(",")[0]
                    .strip()
                    .split(" ")[0]
                )



            if looks_like_menu(value):

                return normalize_url(
                    value
                )



    html = str(soup)



    match = re.search(

        r'(/images/[^"\']*?(?:obedove|menu)[^"\']*\.(?:jpg|jpeg|png|webp))',

        html,

        re.IGNORECASE

    )


    if match:

        return normalize_url(
            match.group(1)
        )



    match = re.search(

        r'(https?://[^"\']*?(?:obedove|menu)[^"\']*\.(?:jpg|jpeg|png|webp))',

        html,

        re.IGNORECASE

    )


    if match:

        return match.group(1)



    return None



def get_image_with_retry():


    for attempt in range(1, 4):

        print(
            f"Hľadám obrázok Smíchov pokus {attempt}/3..."
        )


        try:

            soup = download_page()


        except Exception as e:

            print(
                "⚠️ Neplatná odpoveď:",
                e
            )

            time.sleep(5)

            continue



        image_url = find_image(
            soup
        )


        if image_url:

            return image_url



        print(
            "⚠️ Obrázok sa nenašiel"
        )


        time.sleep(5)



    return None



def scrape_smichov():


    print(
        "Načítavam Smíchov..."
    )


    image_url = get_image_with_retry()



    if not image_url:


        print(
            "⚠️ Smíchov obrázok nedostupný"
        )


        return {

            "restaurant": "Smíchov",

            "type": "image_menu",

            "image_url": "",

            "soup": "",

            "meals": []

        }



    try:

        print(
            "Spúšťam Smíchov OCR..."
        )


        text = extract_text_from_image(
            image_url
        )


        if not text:

            raise Exception(
                "OCR vrátil prázdny text"
            )



        result = parse_smichov_menu(
            text
        )



        if not result:

            raise Exception(
                "Parser vrátil prázdny výsledok"
            )



        if len(result.get("meals", [])) < 2:

            raise Exception(
                "OCR nenašlo dostatok menu položiek"
            )



        result["restaurant"] = "Smíchov"

        result["type"] = "ocr_menu"



        return result



    except Exception as e:


        print(
            "⚠️ Smíchov OCR zlyhalo:",
            e
        )


        print(
            "Používam iba obrázok menu"
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