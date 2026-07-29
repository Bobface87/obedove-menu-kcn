import re
import json
import requests

from bs4 import BeautifulSoup

from ocr import extract_text_from_image


URL = "https://www.buganka.sk/obedove-menu"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; x64) "
        "AppleWebKit/537.36 "
        "Chrome/137 Safari/537.36"
    )
}



def clean_line(line):

    line = line.strip()

    line = re.sub(
        r"^[•·.\-\s]+",
        "",
        line
    )

    line = re.sub(
        r"^[eE]\s+",
        "",
        line
    )

    line = re.sub(
        r"^[0-9\"“”+.\s]+",
        "",
        line
    )

    return line.strip()



def normalize_text(text):

    text = text.replace(
        "cená",
        "cena"
    )

    text = text.replace(
        "Ň",
        ""
    )

    text = re.sub(
        r"M[ÚU]ČN\s*IKY",
        "MÚČNIKY",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"HLAVNE\s+J\s*EDLA",
        "HLAVNÉ JEDLÁ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"HLAVN[ÉE]\s+JEDL[ÁA]",
        "HLAVNÉ JEDLÁ",
        text,
        flags=re.IGNORECASE
    )

    return text



def find_image():

    print(
        "Načítavam Buganku..."
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


        if (
            "buganka" in src.lower()
            and "logo" not in src.lower()
        ):

            return src


    raise Exception(
        "Obrázok Buganky sa nenašiel"
    )



def extract_section(
        text,
        start,
        end=None
):

    match = re.search(
        start,
        text,
        re.IGNORECASE
    )


    if not match:

        return ""


    block = text[
        match.end():
    ]


    if end:

        end_match = re.search(
            end,
            block,
            re.IGNORECASE
        )


        if end_match:

            block = block[
                :end_match.start()
            ]


    return block.strip()



def split_bullets(block):

    result = []


    bad_words = [

        "jedlá, na ktorých",
        "chute, na ktoré",
        "je legenda",
        "starej mamy",
        "t©",
        "šš",
        "%%",
        "532"

    ]


    for line in block.splitlines():

        line = clean_line(
            line
        )


        if not line:

            continue


        if re.search(
            r"cena\s*\d+,\d+",
            line,
            re.IGNORECASE
        ):

            continue


        if any(
            x in line.lower()
            for x in bad_words
        ):

            continue


        if len(line) < 3:

            continue


        result.append(
            line
        )


    return result



def merge_meal_lines(items):

    result = []

    current = ""


    for item in items:

        item = item.strip()


        if not item:

            continue


        starts_new = item[0].isupper()


        if starts_new:

            if current:

                result.append(
                    current.strip()
                )

            current = item


        else:

            current += " " + item


    if current:

        result.append(
            current.strip()
        )


    return result



def extract_price(text):

    match = re.search(
        r"cena\s+(\d+,\d+)\s*€",
        text,
        re.IGNORECASE
    )


    if match:

        return match.group(1) + " €"


    return ""



def parse_buganka_menu(text):


    text = normalize_text(
        text
    )


    soup_block = extract_section(
        text,
        r"POLIEVKY",
        r"HLAVNÉ\s+JEDLÁ"
    )


    meals_block = extract_section(
        text,
        r"HLAVNÉ\s+JEDLÁ",
        r"MÚČNIKY"
    )


    dessert_block = extract_section(
        text,
        r"MÚČNIKY"
    )


    soups = split_bullets(
        soup_block
    )


    meals = split_bullets(
        meals_block
    )


    meals = merge_meal_lines(
        meals
    )


    desserts = split_bullets(
        dessert_block
    )


    desserts = [

        x for x in desserts

        if "sliv" in x.lower()

    ]


    return {


    "restaurant": "Buganka",

    "type": "ocr_menu",

        "soup": {

            "price": extract_price(
                soup_block
            ),

            "items": soups

        },


        "meals": {

            "price": extract_price(
                meals_block
            ),

            "items": meals

        },


        "dessert": {

            "price": extract_price(
                dessert_block
            ),

            "items": desserts

        }

    }



def scrape_buganka():


    image_url = find_image()


    print(
        "Obrázok:"
    )

    print(
        image_url
    )


    print(
        "\nSpúšťam Buganka OCR...\n"
    )


    text = extract_text_from_image(
        image_url
    )


    print(
        "===== OCR TEXT ====="
    )

    print(
        text
    )

    print(
        "===== KONIEC OCR =====\n"
    )


    result = parse_buganka_menu(
        text
    )


    result["restaurant"] = "Buganka"

    result["type"] = "ocr_menu"


    # zámerne NEPRIDÁVAME image_url
    # pri úspešnom OCR nechceme zobrazovať obrázok


    return result



if __name__ == "__main__":


    result = scrape_buganka()


    print(
        "\n===== JSON ====="
    )


    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )