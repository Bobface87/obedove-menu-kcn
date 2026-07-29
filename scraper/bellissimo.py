import requests
from bs4 import BeautifulSoup
from datetime import datetime


from ocr import extract_text_from_image
from bellissimo_ocr_parser import parse_bellissimo_menu



URL = "https://bellissimonitra.com/obedove-menu/"



HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137 Safari/537.36"
    )
}



DAY_NAMES = {

    0: "Pondelok",
    1: "Utorok",
    2: "Streda",
    3: "Štvrtok",
    4: "Piatok"

}





def today_name():

    return DAY_NAMES.get(
        datetime.now().weekday()
    )







def find_menu_image():

    print(
        "Načítavam Bellissimo stránku..."
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



    for img in soup.find_all("img"):


        src = img.get(

            "src",

            ""

        )



        if "menu-bellissimo" in src.lower():


            print(

                "Bellissimo obrázok:",

                src

            )


            return src





    raise Exception(

        "Obrázok menu Bellissimo sa nenašiel"

    )









def scrape_bellissimo():


    print(

        "Načítavam Bellissimo..."

    )



    image_url = find_menu_image()





    try:


        print(

            "Spúšťam Bellissimo OCR..."

        )



        text = extract_text_from_image(

            image_url

        )



        day = today_name()



        if not day:


            raise Exception(

                "Dnes nie je pracovný deň"

            )





        menu = parse_bellissimo_menu(

            text,

            day

        )





        print(

            "Bellissimo OCR položiek:",

            len(menu.get("meals", []))

        )





        #
        # ochrana OCR
        # ak nič nenašlo, necháme aspoň obrázok
        #


        if not menu.get("meals"):


            raise Exception(

                "Bellissimo OCR nenašlo menu"

            )





        return {


            "restaurant": "Bellissimo",


            "type": "ocr_menu",


            "image_url": image_url,


            "starter": menu.get(

                "starter",

                ""

            ),


            "soup": menu.get(

                "soup",

                ""

            ),


            "meals": menu.get(

                "meals",

                []

            )


        }






    except Exception as e:


        print(

            "⚠ Bellissimo OCR chyba:",

            e

        )



        #
        # ZÁLOHA
        # aspoň obrázok zostane
        #


        return {


            "restaurant": "Bellissimo",


            "type": "image_menu",


            "image_url": image_url,


            "starter": "",


            "soup": "",


            "meals": []

        }