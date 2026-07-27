import requests

from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin


from ocr import extract_text_from_image
from ocr_parser import parse_menu_text



URL = "https://www.quovadisnitra.sk/tyzdenne-menu/"



HEADERS = {

    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137 Safari/537.36"
    ),

    "Accept-Language":
        "sk-SK,sk;q=0.9,en;q=0.8"

}



def today_index():

    weekday = datetime.today().weekday()

    if 0 <= weekday < 5:

        return weekday

    return None



def download_page():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )


    print(
        "HTTP STATUS:",
        response.status_code
    )


    response.raise_for_status()


    return BeautifulSoup(
        response.text,
        "html.parser"
    )



def extract_images(soup):

    images = []


    for img in soup.find_all("img"):


        src = img.get("src")


        if not src:

            continue



        full_url = urljoin(
            URL,
            src
        )



        if "wp-content/uploads" in full_url and (

            ".jpg" in full_url.lower()

            or ".jpeg" in full_url.lower()

            or ".png" in full_url.lower()

        ):


            if full_url not in images:

                images.append(full_url)



    return images



def find_today_image():


    soup = download_page()


    images = extract_images(
        soup
    )


    print()
    print(
        "===== QUO VADIS OBRÁZKY ====="
    )


    for img in images:

        print(img)


    print(
        "===== KONIEC OBRÁZKOV ====="
    )
    print()



    if len(images) < 5:

        raise Exception(
            "Nenašlo sa 5 obrázkov menu"
        )



    index = today_index()


    if index is None:

        raise Exception(
            "Dnes nie je pracovný deň"
        )


    return images[index]



def scrape_quovadis():


    print(
        "Načítavam Quo Vadis..."
    )


    image_url = find_today_image()



    print(
        "Spúšťam OCR..."
    )


    text = extract_text_from_image(
        image_url
    )



    parsed = parse_menu_text(
        text
    )



    print(
        "OCR našlo položiek:",
        len(parsed["meals"])
    )



    return {

        "restaurant": "Quo Vadis",

        "type": "ocr_menu",

        "image_url": image_url,

        "starter": parsed["starter"],

        "soup": parsed["soup"],

        "meals": parsed["meals"]

    }