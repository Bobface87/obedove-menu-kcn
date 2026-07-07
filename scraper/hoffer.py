import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime


URL = "https://www.penzion-hoffer.sk/22411/obedove-menu"


def clean_text(text):
    """
    Základné čistenie textu
    """

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



def extract_price(text):
    """
    Vytiahne cenu
    """

    match = re.search(
        r"(\d+,\d+)\s*€",
        text
    )

    if match:
        return match.group(1) + " €"

    return ""



def extract_allergens(text):
    """
    Vytiahne alergény zo zátvoriek
    napr. (1,3,7)
    """

    match = re.search(
        r"\(([\d,\s]+)\)",
        text
    )

    if match:
        return match.group(1).replace(" ", "")

    return ""



def clean_food_text(text):
    """
    Čistenie názvov jedál
    """

    # odstránenie donášky pri dezerte
    text = re.sub(
        r"NEPLATÍ PRE DONÁŠKU\s*-\s*",
        "",
        text,
        flags=re.IGNORECASE
    )


    # odstránenie alergénov
    text = re.sub(
        r"\([\d,\s]+\)",
        "",
        text
    )


    # odstránenie gramáže na začiatku
    text = re.sub(
        r"^\d+\s*g\s*",
        "",
        text,
        flags=re.IGNORECASE
    )


    text = clean_text(text)

    return text



def find_today_block(lines):
    """
    Nájde dnešný deň podľa dátumu
    """

    today = datetime.now()

    date_pattern = today.strftime("%d.%m.%Y")

    start = None


    for i, line in enumerate(lines):

        if date_pattern in line:

            start = i
            break


    if start is None:

        return lines


    result = []


    for line in lines[start:]:

        if (
            line.startswith("Pondelok")
            or line.startswith("Utorok")
            or line.startswith("Streda")
            or line.startswith("Štvrtok")
            or line.startswith("Piatok")
        ):

            if result:

                break


        result.append(line)


    return result



def scrape_hoffer():

    print("Načítavam Hoffera...")


    headers = {
        "User-Agent": "Mozilla/5.0"
    }


    response = requests.get(
        URL,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    content = soup.find(
        "main"
    )


    if not content:

        content = soup


    raw_text = content.get_text(
        "\n",
        strip=True
    )


    print("===== HOFFER RAW =====")
    print(raw_text[:3000])
    print("===== KONIEC HOFFER RAW =====")


    lines = [
        clean_text(x)
        for x in raw_text.split("\n")
        if clean_text(x)
    ]


    lines = find_today_block(lines)


    soup_name = ""
    soup_allergens = ""

    meals = []

    dessert = None


    current_menu = None


    for i, line in enumerate(lines):


        # POLIEVKA

        if line.upper() == "POLIEVKA":

            if i + 1 < len(lines):

                soup_line = lines[i + 1]

                soup_name = clean_food_text(
                    soup_line
                )

                soup_allergens = extract_allergens(
                    soup_line
                )


            continue



        # MENU ČÍSLO

        menu_match = re.match(
            r"(\d+)\.\)",
            line
        )


        if menu_match:

            current_menu = int(
                menu_match.group(1)
            )


            continue



        # CENA + NASLEDUJÚCE JEDLO

        if current_menu:

            if re.search(
                r"\d+,\d+\s*€",
                line
            ):

                price = extract_price(line)


                if i + 1 < len(lines):

                    food_line = lines[i + 1]

                    meals.append(
                        {
                            "menu": current_menu,
                            "name": clean_food_text(food_line),
                            "price": price,
                            "allergens": extract_allergens(food_line)
                        }
                    )


                current_menu = None


                continue



        # DEZERT

        if line.upper() == "DEZERT":

            if i + 1 < len(lines):

                dessert_line = lines[i + 1]


                weight_match = re.search(
                    r"(\d+g)",
                    dessert_line,
                    flags=re.IGNORECASE
                )


                weight = ""

                if weight_match:

                    weight = weight_match.group(1)


                dessert = {
                    "name": clean_food_text(dessert_line),
                    "weight": weight,
                    "allergens": extract_allergens(dessert_line),
                    "delivery": False
                }


            continue



    return {
        "restaurant": "Hoffer",
        "soup": soup_name,
        "soup_allergens": soup_allergens,
        "meals": meals[:5],
        "dessert": dessert
    }



if __name__ == "__main__":

    print(
        scrape_hoffer()
    )