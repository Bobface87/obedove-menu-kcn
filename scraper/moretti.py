import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


URL = "http://www.pensionemoretti.sk/index.php/sk/denne-menu.html"


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

    return text.strip()



def extract_allergens(text):

    match = re.search(
        r"\(([\d,\s]+)\)",
        text
    )

    if match:

        return re.sub(
            r"\s+",
            "",
            match.group(1)
        )

    return ""



def remove_allergens(text):

    return re.sub(
        r"\([\d,\s]+\)",
        "",
        text
    )



def extract_price(text):

    match = re.search(
        r"(\d+,\d+)\s*€",
        text
    )

    if match:

        return match.group(1) + " €"

    return ""



def remove_price(text):

    return re.sub(
        r"\d+,\d+\s*€",
        "",
        text
    )



def get_today_marker():

    today = datetime.today()

    weekday = today.strftime("%A")


    if weekday not in DAYS:

        return None


    date = (
        str(today.day)
        +
        "."
        +
        str(today.month)
        +
        "."
        +
        str(today.year)
    )


    return (
        DAYS[weekday]
        +
        ": "
        +
        date
    )



def parse_soup(text):

    allergens = extract_allergens(
        text
    )


    name = text.replace(
        "Polievka:",
        ""
    )


    name = remove_allergens(
        name
    )


    return {

        "name": clean_text(name),

        "allergens": allergens

    }



def parse_meal(text, number):

    allergens = extract_allergens(
        text
    )


    price = extract_price(
        text
    )


    name = remove_allergens(
        text
    )


    name = remove_price(
        name
    )


    return {

        "menu": str(number),

        "name": clean_text(name),

        "allergens": allergens,

        "price": price

    }



def scrape_moretti():

    print("Načítavam Moretti...")


    r = requests.get(
        URL,
        timeout=20
    )


    r.encoding = "utf-8"


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    text = clean_text(
        soup.get_text(
            "\n",
            strip=True
        )
    )


    marker = get_today_marker()


    if not marker:

        raise Exception(
            "Dnes nie je pracovný deň"
        )


    start = text.find(
        marker
    )


    if start == -1:

        raise Exception(
            "Dnešné menu Moretti nenájdené"
        )


    section = text[start:]


    end = section.find(
        "Ak ste si nevybrali"
    )


    if end != -1:

        daily = section[:end]

        weekly = section[end:]

    else:

        daily = section

        weekly = ""



    soup_match = re.search(
        r"Polievka:.*?(?=\s+\d:)",
        daily
    )


    soup_data = None


    if soup_match:

        soup_data = parse_soup(
            soup_match.group(0)
        )



    meals = []



    # MENU 1-6

    for match in re.finditer(
        r"(\d+):\s*(.*?)(?=\s+\d+:|\Z)",
        daily
    ):


        number = int(
            match.group(1)
        )


        if 1 <= number <= 6:

            meals.append(
                parse_meal(
                    match.group(2),
                    number
                )
            )



    # TYZDENNA PONUKA 7-11

    weekly_text = weekly.split(
        "Alergény:"
    )[0]


    # odstráni úvodnú vetu:
    # "Ak ste si nevybrali z ponuky nášho denného menu,
    # máme pre Vás na celý týždeň:"

    weekly_text = re.sub(
        r"^.*?celý týždeň:",
        "",
        weekly_text,
        flags=re.I | re.S
    )


    weekly_items = re.findall(
        r"(.+?)\s+(\d+,\d+€)",
        weekly_text
    )


    number = 7


    for item, price in weekly_items:


        if number > 11:

            break


        meals.append(
            parse_meal(
                item + " " + price,
                number
            )
        )


        number += 1



    return {

        "restaurant": "Moretti",

        "type": "classic_menu",

        "soup": soup_data,

        "meals": meals

    }



def main():

    import json


    data = scrape_moretti()


    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )



if __name__ == "__main__":

    main()