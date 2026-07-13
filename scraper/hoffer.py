import requests
from bs4 import BeautifulSoup
import re


MAIN_URL = "https://www.penzion-hoffer.sk/18614/zamocka-koruna-u-hoffera"



def find_menu_url():

    print("🔎 Hľadám aktuálne Hoffer obedové menu...")


    headers = {
        "User-Agent": "Mozilla/5.0"
    }


    response = requests.get(
        MAIN_URL,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link["href"]

        text = link.get_text(
            " ",
            strip=True
        ).lower()


        if (
            "obedové menu" in text
            or "obedove menu" in text
        ):

            if href.startswith("/"):

                href = (
                    "https://www.penzion-hoffer.sk"
                    + href
                )


            print(
                "Hoffer menu URL:",
                href
            )


            return href



    raise Exception(
        "Hoffer obedové menu sa nenašlo"
    )



def extract_price(text):

    match = re.search(
        r"(\d+,\d+)\s*€",
        text
    )

    if match:

        return match.group(1) + " €"

    return None



def clean_text(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



def remove_allergens(text):

    return re.sub(
        r"\s*\(\d+(?:,\d+)*\)\s*$",
        "",
        text
    ).strip()



def extract_allergens(text):

    match = re.search(
        r"\((\d+(?:,\d+)*)\)\s*$",
        text
    )

    if match:

        return match.group(1)

    return None



def scrape_hoffer():

    print("Načítavam Hoffera...")


    url = find_menu_url()


    headers = {
        "User-Agent": "Mozilla/5.0"
    }


    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    content = soup.find("main")


    if not content:

        content = soup



    text = content.get_text(
        "\n",
        strip=True
    )


    lines = [
        clean_text(x)
        for x in text.split("\n")
        if clean_text(x)
    ]


    soup_text = ""

    meals = []

    dessert = None


    current_menu = None



    for index, line in enumerate(lines):


        if line.upper() == "POLIEVKA":

            if index + 1 < len(lines):

                soup_text = remove_allergens(
                    lines[index + 1]
                )

            continue



        menu_match = re.match(
            r"(\d+)\.\)",
            line
        )


        if menu_match:

            current_menu = int(
                menu_match.group(1)
            )

            continue



        if current_menu and re.match(
            r"\d+,\d+\s*€",
            line
        ):


            price = extract_price(
                line
            )


            if index + 1 < len(lines):

                meal_line = lines[index + 1]


                meal_line = re.sub(
                    r"^\d+g\s*",
                    "",
                    meal_line
                )


                meal_line = remove_allergens(
                    meal_line
                )


                meals.append(
                    {
                        "menu": current_menu,
                        "name": meal_line,
                        "price": price
                    }
                )


            current_menu = None

            continue



        if line.upper() == "DEZERT":

            if index + 1 < len(lines):

                dessert_line = lines[index + 1]


                delivery = True


                if "NEPLATÍ PRE DONÁŠKU" in dessert_line.upper():

                    delivery = False


                    dessert_line = re.sub(
                        r"NEPLATÍ PRE DONÁŠKU\s*-\s*",
                        "",
                        dessert_line,
                        flags=re.IGNORECASE
                    )


                weight = None


                weight_match = re.search(
                    r"(\d+g)",
                    dessert_line
                )


                if weight_match:

                    weight = weight_match.group(1)

                    dessert_line = dessert_line.replace(
                        weight,
                        "",
                        1
                    )


                dessert_line = remove_allergens(
                    dessert_line
                )


                dessert = {
                    "name": dessert_line.strip(),
                    "weight": weight,
                    "delivery": delivery
                }



    return {
        "restaurant": "Hoffer",
        "soup": soup_text,
        "meals": meals[:5],
        "dessert": dessert
    }