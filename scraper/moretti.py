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

    return (
        DAYS[weekday]
        + ": "
        + str(today.day)
        + "."
        + str(today.month)
        + "."
        + str(today.year)
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


def get_page_lines():

    r = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=20,
        verify=False
    )

    r.raise_for_status()

    # Moretti má nesprávne/staré deklarované kódovanie.
    # Obsah stránky je v skutočnosti UTF-8.
    html = r.content.decode(
        "utf-8",
        errors="replace"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    raw_lines = soup.get_text(
        "\n",
        strip=True
    ).splitlines()

    lines = []

    for line in raw_lines:

        line = clean_text(
            line
        )

        if line:

            lines.append(
                line
            )

    return lines


def find_today_section(lines):

    marker = get_today_marker()

    if not marker:

        raise Exception(
            "Dnes nie je pracovný deň"
        )

    start = -1

    for index, line in enumerate(lines):

        # Moretti má dátum v HTML rozdelený:
        #
        # Pondelok: 10
        # .8.2026
        #
        # Preto kontrolujeme obe možnosti.

        if line == marker:

            start = index

            break

        if line.startswith(
            DAYS.get(
                datetime.today().strftime("%A"),
                ""
            )
            + ": "
        ):

            if index + 1 < len(lines):

                combined = (
                    line
                    +
                    lines[index + 1]
                )

                if combined == marker:

                    start = index

                    break

    if start == -1:

        raise Exception(
            "Dnešné menu Moretti nenájdené"
        )

    today_lines = []

    index = start + 1

    # Ak bol dátum rozdelený na dva riadky,
    # preskočíme aj druhý riadok dátumu.

    if (
        start + 1 < len(lines)
        and re.match(
            r"^\.\d+\.\d+$",
            lines[start + 1]
        )
    ):

        index += 1

    while index < len(lines):

        line = lines[index]

        # Ďalší pracovný deň.
        if re.match(
            r"^(Pondelok|Utorok|Streda|Štvrtok|Piatok):",
            line
        ):

            break

        # Týždenná ponuka.
        if line.startswith(
            "Ak ste si nevybrali"
        ):

            break

        # Alergény.
        if line.startswith(
            "Alergény:"
        ):

            break

        if line.startswith(
            "Prajeme Vám dobrú chuť"
        ):

            break

        today_lines.append(
            line
        )

        index += 1

    return today_lines


def find_weekly_section(lines):

    start = -1

    for index, line in enumerate(lines):

        if line.startswith(
            "Ak ste si nevybrali"
        ):

            start = index

            break

    if start == -1:

        return []

    weekly_lines = []

    for line in lines[start + 1:]:

        if line.startswith(
            "Alergény:"
        ):

            break

        if line.startswith(
            "Prajeme Vám"
        ):

            break

        weekly_lines.append(
            line
        )

    return weekly_lines


def parse_today_menu(lines):

    soup_data = None

    meals = []

    for line in lines:

        if line.startswith(
            "Polievka:"
        ):

            soup_data = parse_soup(
                line
            )

            continue

        match = re.match(
            r"^([1-6]):\s*(.*)$",
            line
        )

        if not match:

            continue

        number = int(
            match.group(1)
        )

        text = match.group(2)

        meals.append(
            parse_meal(
                text,
                number
            )
        )

    return soup_data, meals


def parse_weekly_menu(lines):

    meals = []

    number = 7

    for line in lines:

        if number > 11:

            break

        line = clean_text(
            line
        )

        if not line:

            continue

        match = re.match(
            r"^(.*?)\s+(\d+,\d+)\s*€$",
            line
        )

        if not match:

            continue

        name = match.group(1)

        price = (
            match.group(2)
            + " €"
        )

        meals.append(
            parse_meal(
                name + " " + price,
                number
            )
        )

        number += 1

    return meals


def scrape_moretti():

    print(
        "Načítavam Moretti..."
    )

    lines = get_page_lines()

    today_lines = find_today_section(
        lines
    )

    weekly_lines = find_weekly_section(
        lines
    )

    soup_data, daily_meals = parse_today_menu(
        today_lines
    )

    weekly_meals = parse_weekly_menu(
        weekly_lines
    )

    meals = (
        daily_meals
        +
        weekly_meals
    )

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