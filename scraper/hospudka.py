import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


URL = "https://www.hospudkauslovaka.sk/"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137 Safari/537.36"
    )
}


def download_page():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )



def clean_text(text):

    return (
        text
        .replace("\xa0", " ")
        .strip()
    )



def get_today_name():

    days = {
        0: "pondelok",
        1: "utorok",
        2: "streda",
        3: "štvrtok",
        4: "piatok"
    }

    return days.get(
        datetime.today().weekday()
    )



def normalize_day(text):

    """
    Pondelok
    Pondelok 1
    Pondelok 2

    -> pondelok
    """

    text = clean_text(text).lower()

    match = re.match(
        r"^(pondelok|utorok|streda|štvrtok|piatok)",
        text
    )

    if match:
        return match.group(1)

    return ""



def find_today_block(soup):

    today = get_today_name()

    if not today:
        return None


    wrappers = soup.find_all(
        class_="daily-menu-wrapper"
    )


    for wrapper in wrappers:

        parent = wrapper.parent


        for heading in parent.find_all("h1"):

            day = normalize_day(
                heading.get_text()
            )


            if day == today:

                return wrapper


    return None



def extract_menu_block(parent, menu_number):

    for heading in parent.find_all("h1"):

        title = clean_text(
            heading.get_text()
        )


        if title == f"Menu {menu_number}":

            container = heading.parent.parent


            texts = container.find_all(
                class_="ct-text-block"
            )


            if texts:

                name = clean_text(
                    texts[-1].get_text()
                )


                price = ""


                for item in container.find_all("h1"):

                    value = clean_text(
                        item.get_text()
                    )


                    if "€" in value:

                        price = value
                        break


                return {
                    "menu": menu_number,
                    "name": name,
                    "price": price
                }


    return None



def extract_soup(parent):

    for heading in parent.find_all("h1"):

        if clean_text(
            heading.get_text()
        ) == "Polievka":


            container = heading.parent.parent


            texts = container.find_all(
                class_="ct-text-block"
            )


            if texts:

                return clean_text(
                    texts[-1].get_text()
                )


    return ""



def scrape_daily_menu(soup):

    meals = []


    daily = find_today_block(
        soup
    )


    if not daily:

        raise Exception(
            "Aktuálny deň sa nenašiel"
        )


    soup_text = extract_soup(
        daily
    )


    added = set()


    # iba menu 1 a 2
    for number in [1, 2]:

        item = extract_menu_block(
            daily,
            number
        )


        if item:

            key = (
                item["menu"],
                item["name"]
            )


            if key not in added:

                meals.append(
                    item
                )

                added.add(
                    key
                )


    if not meals:

        raise Exception(
            "Denné menu sa nenašlo"
        )


    return soup_text, meals



def scrape_permanent_menu(soup):

    result = []


    title = None


    for heading in soup.find_all("h1"):

        if "Stála ponuka menu" in clean_text(
            heading.get_text()
        ):

            title = heading
            break



    if not title:

        return result



    container = title.parent.parent



    for number in range(4, 9):

        item = extract_menu_block(
            container,
            number
        )


        if item:

            result.append(
                item
            )


    return result



def scrape_hospudka():

    print(
        "Načítavam Hospúdku..."
    )


    soup = download_page()


    daily_soup, meals = scrape_daily_menu(
        soup
    )


    permanent = scrape_permanent_menu(
        soup
    )


    meals.extend(
        permanent
    )


    return {
        "restaurant": "Hospúdka u Slováka",
        "soup": daily_soup,
        "meals": meals
    }