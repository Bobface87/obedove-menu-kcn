import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


URL = "https://www.ukrba.sk/sk/denne-menu"


DAYS = {
    "Monday": "Pondelok",
    "Tuesday": "Utorok",
    "Wednesday": "Streda",
    "Thursday": "Štvrtok",
    "Friday": "Piatok"
}


def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = text.strip()


    # oprava rozbitých gramáží
    # napr. 20 0g -> 200g
    text = re.sub(
        r"(\d)\s+(\d)g",
        r"\1\2g",
        text
    )


    return text



def extract_allergens(text):

    match = re.search(
        r"\(([\d,]+)\)",
        text
    )


    if match:

        return match.group(1)


    return ""



def extract_price(text):

    match = re.search(
        r"(\d+,\d+)\s*€",
        text
    )


    if match:

        return match.group(1) + " €"


    return None



def remove_price(text):

    return re.sub(
        r"\d+,\d+\s*€",
        "",
        text
    ).strip()



def remove_allergens(text):

    return re.sub(
        r"\([\d,]+\)",
        "",
        text
    ).strip()



def get_today_label():

    today = datetime.today()

    weekday = today.strftime("%A")


    if weekday not in DAYS:

        return None


    day_name = DAYS[weekday]


    date = today.strftime(
        "%d.%m.%Y"
    )


    # stránka používa napr. 7.8.2026
    date = date.lstrip("0").replace(
        ".0",
        "."
    )


    return f"{day_name} {date}"



def parse_menu_items(items, start_number=1):

    meals = []

    number = start_number


    for item in items:

        text = clean_text(
            item.get_text(
                " ",
                strip=True
            )
        )


        if not text:

            continue


        allergens = extract_allergens(
            text
        )


        price = extract_price(
            text
        )


        name = remove_price(
            text
        )


        name = remove_allergens(
            name
        )


        meals.append(
            {
                "menu": str(number),
                "name": name,
                "allergens": allergens,
                "price": price
            }
        )


        number += 1


    return meals



def parse_extra_menu(text, number):

    allergens = extract_allergens(
        text
    )


    name = remove_price(
        text[2:]
    )


    name = remove_allergens(
        name
    )


    return {

        "menu": str(number),

        "name": name,

        "allergens": allergens,

        "price": extract_price(text)

    }



def scrape_ukrba():

    response = requests.get(
        URL,
        timeout=20
    )


    response.encoding = "utf-8"


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    paragraphs = soup.find_all(
        "p"
    )


    today_label = get_today_label()


    if not today_label:

        return None



    start_index = None


    for i, p in enumerate(paragraphs):

        text = clean_text(
            p.get_text(
                " ",
                strip=True
            )
        )


        if today_label in text:

            start_index = i

            break



    if start_index is None:


        return {

            "restaurant": "U Krba",

            "type": "classic_menu",

            "error": "Dnešné menu nenájdené"

        }



    soup_data = {

        "name": "",

        "allergens": None

    }


    meals = []



    # polievka

    for p in paragraphs[start_index + 1:]:


        text = clean_text(
            p.get_text(
                " ",
                strip=True
            )
        )


        if text.startswith(
            "Polievka"
        ):


            soup_text = text.replace(
                "Polievka:",
                ""
            ).strip()


            soup_text = re.sub(
                r"^\d+,\d+l\s*",
                "",
                soup_text
            )


            soup_data["allergens"] = extract_allergens(
                soup_text
            )


            soup_data["name"] = remove_allergens(
                soup_text
            )


            break




    # menu 1-3

    ol = None


    for tag in soup.find_all("ol"):


        previous = tag.find_previous(
            "p"
        )


        if previous:

            try:

                index = paragraphs.index(
                    previous
                )


                if index >= start_index:

                    ol = tag

                    break


            except ValueError:

                pass



    if ol:


        meals.extend(
            parse_menu_items(
                ol.find_all("li"),
                1
            )
        )



    # menu 4-5

    extra_started = False


    for p in paragraphs:


        text = clean_text(
            p.get_text(
                " ",
                strip=True
            )
        )


        if "Pre tých" in text:

            extra_started = True

            continue



        if extra_started:


            if text.startswith("4."):


                meals.append(
                    parse_extra_menu(
                        text,
                        4
                    )
                )



            elif text.startswith("5."):


                meals.append(
                    parse_extra_menu(
                        text,
                        5
                    )
                )


                break



    return {

        "restaurant": "U Krba",

        "type": "classic_menu",

        "soup": soup_data,

        "meals": meals

    }