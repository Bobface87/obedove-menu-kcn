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

    # bežný zápis:
    # (1,3,7)
    #
    # prípadne rozbitý:
    # (1.3,7)

    match = re.search(
        r"\(([\d,\.]+)\)",
        text
    )

    if match:

        allergens = match.group(1)

        allergens = allergens.replace(
            ".",
            ","
        )

        return allergens

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
        r"\([\d,\.]+\)",
        "",
        text
    ).strip()


def get_today_pattern():

    today = datetime.today()

    weekday = today.strftime("%A")

    if weekday not in DAYS:

        return None

    day_name = DAYS[weekday]

    # stránka môže mať napr.:
    #
    # Pondelok 10 .8.2026
    #
    # alebo:
    #
    # Pondelok 10. 8.2026
    #
    # alebo:
    #
    # Pondelok 10.8.2026

    return re.compile(

        rf"{day_name}"
        rf"\s*"
        rf"{today.day}"
        rf"\s*\.\s*"
        rf"{today.month}"
        rf"\s*\.\s*"
        rf"{today.year}",

        re.IGNORECASE

    )


def find_today_block(full_text):

    pattern = get_today_pattern()

    if not pattern:

        return None

    today_match = pattern.search(
        full_text
    )

    if not today_match:

        return None

    start = today_match.end()

    # --------------------------------------------------
    # nájdeme začiatok ďalšieho pracovného dňa
    # --------------------------------------------------

    next_day_pattern = re.compile(

        r"(Pondelok|Utorok|Streda|Štvrtok|Piatok)"
        r"\s*"
        r"\d{1,2}"
        r"\s*\.\s*"
        r"\d{1,2}"
        r"\s*\.\s*"
        r"\d{4}",

        re.IGNORECASE

    )

    next_match = None

    for match in next_day_pattern.finditer(
        full_text,
        start
    ):

        next_match = match

        break

    if next_match:

        end = next_match.start()

    else:

        end = len(full_text)

    return full_text[
        start:end
    ]


def parse_meal_text(text, number):

    text = clean_text(
        text
    )

    if not text:

        return None

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

    name = clean_text(
        name
    )

    if not name:

        return None

    return {

        "menu": str(number),

        "name": name,

        "allergens": allergens,

        "price": price

    }


def parse_today_meals(today_text):

    meals = []

    # --------------------------------------------------
    # odstránime polievku
    #
    # od "Polievka:" po prvú položku začínajúcu
    # gramážou, napr. 150g / 350g
    # --------------------------------------------------

    soup_end = re.search(

        r"\bPolievka\s*:?.*?"
        r"(?=\s+\d+\s*g\b)",

        today_text,

        re.IGNORECASE

    )

    if soup_end:

        meals_text = today_text[
            soup_end.end():
        ]

    else:

        meals_text = today_text

    # --------------------------------------------------
    # nájdeme začiatky jednotlivých jedál
    #
    # napr.:
    #
    # 150g Medovo-horčicové...
    # 350g Bryndzové halušky...
    # 150g Grilovaný pstruh...
    #
    # --------------------------------------------------

    matches = list(

        re.finditer(

            r"(?<!\d)"
            r"(\d+)\s*g\b",

            meals_text,

            re.IGNORECASE

        )

    )

    number = 1

    for index, match in enumerate(matches):

        start = match.start()

        if index + 1 < len(matches):

            end = matches[
                index + 1
            ].start()

        else:

            end = len(meals_text)

        meal_text = meals_text[
            start:end
        ]

        meal = parse_meal_text(
            meal_text,
            number
        )

        if meal:

            meals.append(
                meal
            )

            number += 1

    # --------------------------------------------------
    # nechceme viac ako 3 denné menu
    # --------------------------------------------------

    meals = meals[:3]

    return meals


def parse_extra_menu(text, number):

    text = clean_text(
        text
    )

    # odstránenie čísla:
    #
    # 4. 150g ...
    # 5. 350g ...

    text = re.sub(
        r"^\d+\.\s*",
        "",
        text
    )

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

    name = clean_text(
        name
    )

    return {

        "menu": str(number),

        "name": name,

        "allergens": allergens,

        "price": price

    }


def parse_soup(today_text):

    soup_data = {

        "name": "",

        "allergens": None

    }

    soup_match = re.search(

        r"Polievka"
        r"\s*:?\s*"
        r"(.*?)"
        r"(?=\s+\d+\s*g\b)",

        today_text,

        re.IGNORECASE

    )

    if not soup_match:

        return soup_data

    soup_text = clean_text(
        soup_match.group(1)
    )

    # odstránenie objemu:
    #
    # 0,33l
    # 0,33 l

    soup_text = re.sub(

        r"^\d+,\d+\s*l\s*",

        "",

        soup_text,

        flags=re.IGNORECASE

    )

    soup_data[
        "allergens"
    ] = extract_allergens(
        soup_text
    )

    soup_data[
        "name"
    ] = clean_text(
        remove_allergens(
            soup_text
        )
    )

    return soup_data


def scrape_ukrba():

    print(
        "Načítavam U Krba..."
    )

    response = requests.get(

        URL,

        timeout=20,

        headers={
            "User-Agent":
            "Mozilla/5.0"
        }

    )

    response.raise_for_status()

    response.encoding = "utf-8"

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # --------------------------------------------------
    # celý text stránky
    # --------------------------------------------------

    full_text = clean_text(

        soup.get_text(
            " ",
            strip=True
        )

    )

    # --------------------------------------------------
    # dnešný blok
    # --------------------------------------------------

    today_text = find_today_block(
        full_text
    )

    if not today_text:

        return {

            "restaurant": "U Krba",

            "type": "classic_menu",

            "error":
            "Dnešné menu nenájdené"

        }

    # --------------------------------------------------
    # polievka
    # --------------------------------------------------

    soup_data = parse_soup(
        today_text
    )

    # --------------------------------------------------
    # menu 1-3
    # --------------------------------------------------

    meals = parse_today_meals(
        today_text
    )

    # --------------------------------------------------
    # menu 4-5
    #
    # Univerzálna ponuka je mimo
    # denného bloku.
    # --------------------------------------------------

    paragraphs = soup.find_all(
        "p"
    )

    extra_started = False

    for p in paragraphs:

        text = clean_text(
            p.get_text(
                " ",
                strip=True
            )
        )

        if not text:

            continue

        if "Pre tých" in text:

            extra_started = True

            continue

        if not extra_started:

            continue

        # --------------------------------------------------
        # menu 4
        # --------------------------------------------------

        if re.match(
            r"^4\.\s*",
            text
        ):

            item = parse_extra_menu(
                text,
                4
            )

            if item["name"]:

                if not any(
                    m["menu"] == "4"
                    for m in meals
                ):

                    meals.append(
                        item
                    )

        # --------------------------------------------------
        # menu 5
        # --------------------------------------------------

        elif re.match(
            r"^5\.\s*",
            text
        ):

            item = parse_extra_menu(
                text,
                5
            )

            if item["name"]:

                if not any(
                    m["menu"] == "5"
                    for m in meals
                ):

                    meals.append(
                        item
                    )

            break

    # --------------------------------------------------
    # zoradenie menu
    # --------------------------------------------------

    meals.sort(

        key=lambda x: int(
            x["menu"]
        )

    )

    return {

        "restaurant": "U Krba",

        "type": "classic_menu",

        "soup": soup_data,

        "meals": meals

    }