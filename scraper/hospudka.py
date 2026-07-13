import requests
from bs4 import BeautifulSoup


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



def extract_menu_block(parent, menu_number):

    result = None


    headings = parent.find_all(
        ["h1", "h2"]
    )


    for heading in headings:

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


                price_candidates = container.find_all(
                    ["h1", "h2"]
                )


                for item in price_candidates:

                    value = clean_text(
                        item.get_text()
                    )

                    if "€" in value:

                        price = value


                result = {
                    "menu": menu_number,
                    "name": name,
                    "price": price
                }


                break


    return result



def extract_soup(parent):

    headings = parent.find_all(
        ["h1", "h2"]
    )


    for heading in headings:

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

    daily = soup.find(
        class_="daily-menu-wrapper"
    )


    if not daily:

        raise Exception(
            "Denné menu sa nenašlo"
        )


    soup_text = extract_soup(
        daily
    )


    meals = []


    # iba Menu 1 a Menu 2
    for number in [1, 2]:

        item = extract_menu_block(
            daily,
            number
        )

        if item:

            meals.append(
                item
            )


    return soup_text, meals



def scrape_permanent_menu(soup):

    result = []


    title = None


    for heading in soup.find_all(
        ["h1", "h2"]
    ):

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