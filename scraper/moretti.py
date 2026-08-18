import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import re


URL = "http://www.pensionemoretti.sk/index.php/sk/denne-menu.html"


DAYS = {
    "Monday": "Pondelok",
    "Tuesday": "Utorok",
    "Wednesday": "Streda",
    "Thursday": "Štvrtok",
    "Friday": "Piatok"
}


TIMEZONE = ZoneInfo(
    "Europe/Bratislava"
)


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


def get_today_data():

    """
    Vytvorí dnešný deň a dátum podľa
    slovenského času Europe/Bratislava.

    Príklad:

        day_name:
            Utorok

        day_number:
            18

        month:
            8

        year:
            2026

        date_variants:
            18.8.2026
            18.08.2026
    """

    today = datetime.now(
        TIMEZONE
    )

    weekday = today.strftime(
        "%A"
    )

    if weekday not in DAYS:

        return None

    day_name = DAYS[
        weekday
    ]

    day_number = today.day

    month = today.month

    year = today.year

    date_variants = [
        f"{day_number}.{month}.{year}",
        f"{day_number:02d}.{month:02d}.{year}",
        f"{day_number:02d}.{month}.{year}",
        f"{day_number}.{month:02d}.{year}"
    ]

    return {
        "day_name": day_name,
        "day_number": day_number,
        "month": month,
        "year": year,
        "date_variants": date_variants
    }


def parse_soup(text):

    allergens = extract_allergens(
        text
    )

    name = text.replace(
        "Polievka:",
        ""
    )

    name = name.replace(
        "Polievka :",
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

    """
    Nájde dnešný blok menu.

    Moretti môže dátum zobrazovať napr.:

        Utorok 18.8.2026

    alebo:

        Utorok: 18.8.2026

    alebo môže byť dátum rozdelený:

        Utorok 18
        .8.2026

    Parser preto nevychádza z jedného presného
    textového formátu.

    Dnešný deň a dátum si vytvorí sám podľa
    Europe/Bratislava.
    """

    today_data = get_today_data()

    if not today_data:

        raise Exception(
            "Dnes nie je pracovný deň"
        )

    day_name = today_data[
        "day_name"
    ]

    date_variants = today_data[
        "date_variants"
    ]

    start = -1

    # ----------------------------------------------------
    # 1. Hľadáme deň + dátum v jednom riadku
    # ----------------------------------------------------

    for index, line in enumerate(
        lines
    ):

        # Odstránime prípadnú dvojbodku
        # medzi názvom dňa a dátumom.

        normalized = re.sub(
            r"^"
            + re.escape(day_name)
            + r"\s*:?\s*",
            "",
            line,
            flags=re.IGNORECASE
        )

        normalized = normalized.strip()

        if normalized in date_variants:

            start = index

            break

    # ----------------------------------------------------
    # 2. Dátum môže byť rozdelený na dva riadky
    # ----------------------------------------------------

    if start == -1:

        for index, line in enumerate(
            lines
        ):

            if not re.match(
                r"^"
                + re.escape(day_name)
                + r"\s*:?\s*\d{1,2}$",
                line,
                re.IGNORECASE
            ):

                continue

            if index + 1 >= len(lines):

                continue

            combined = (
                line
                +
                lines[index + 1]
            )

            normalized = re.sub(
                r"^"
                + re.escape(day_name)
                + r"\s*:?\s*",
                "",
                combined,
                flags=re.IGNORECASE
            )

            normalized = normalized.strip()

            if normalized in date_variants:

                start = index

                break

    # ----------------------------------------------------
    # 3. Ak dátum nevieme nájsť presne,
    #    skúsime ešte všeobecný dátumový vzor
    #    v riadku dnešného dňa.
    # ----------------------------------------------------

    if start == -1:

        date_pattern = re.compile(
            r"^"
            + re.escape(day_name)
            + r"\s*:?\s*"
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})"
            r"\s*$",
            re.IGNORECASE
        )

        for index, line in enumerate(
            lines
        ):

            match = date_pattern.match(
                line
            )

            if not match:

                continue

            day_number = int(
                match.group(1)
            )

            month = int(
                match.group(2)
            )

            year = int(
                match.group(3)
            )

            if (
                day_number
                == today_data["day_number"]
                and
                month
                == today_data["month"]
                and
                year
                == today_data["year"]
            ):

                start = index

                break

    # ----------------------------------------------------
    # 4. Dnešný deň sa nenašiel
    # ----------------------------------------------------

    if start == -1:

        raise Exception(
            "Dnešné menu Moretti nenájdené"
        )

    today_lines = []

    index = start + 1

    # ----------------------------------------------------
    # Ak bol dátum rozdelený na dva riadky,
    # preskočíme druhý riadok.
    # ----------------------------------------------------

    if (
        start + 1 < len(lines)
        and re.match(
            r"^\.\d+\.\d+$",
            lines[start + 1]
        )
    ):

        index += 1

    # ----------------------------------------------------
    # Čítame menu dnešného dňa
    # ----------------------------------------------------

    while index < len(lines):

        line = lines[index]

        # Ďalší pracovný deň.
        if re.match(
            r"^(Pondelok|Utorok|Streda|Štvrtok|Piatok)"
            r"\s*:?\s*\d{1,2}\.",
            line,
            re.IGNORECASE
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

        # Koniec menu.
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

    for index, line in enumerate(
        lines
    ):

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

        if (
            line.startswith(
                "Polievka:"
            )
            or
            line.startswith(
                "Polievka :"
            )
        ):

            soup_data = parse_soup(
                line
            )

            continue

        match = re.match(
            r"^([1-6])\s*:\s*(.*)$",
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

    soup_data, daily_meals = (
        parse_today_menu(
            today_lines
        )
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