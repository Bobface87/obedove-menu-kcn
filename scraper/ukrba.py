import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json


URL = "https://www.ukrba.sk/sk/denne-menu"


DAYS = {
    "Monday": "Pondelok",
    "Tuesday": "Utorok",
    "Wednesday": "Streda",
    "Thursday": "Štvrtok",
    "Friday": "Piatok"
}


# --------------------------------------------------
# ČISTENIE TEXTU
# --------------------------------------------------

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
    #
    # napr.:
    # 20 0g -> 200g
    # 15 0g -> 150g
    # 35 0g -> 350g

    text = re.sub(
        r"(\d)\s+(\d)g",
        r"\1\2g",
        text
    )

    return text


# --------------------------------------------------
# ALERGÉNY
# --------------------------------------------------

def extract_allergens(text):

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


def remove_allergens(text):

    return re.sub(
        r"\([\d,\.]+\)",
        "",
        text
    ).strip()


# --------------------------------------------------
# CENA
# --------------------------------------------------

def extract_price(text):

    match = re.search(
        r"(\d+,\d+)\s*€",
        text
    )

    if match:

        return (
            match.group(1)
            + " €"
        )

    return None


def remove_price(text):

    return re.sub(
        r"\d+,\d+\s*€",
        "",
        text
    ).strip()


# --------------------------------------------------
# NÁJDENIE DNEŠNÉHO DÁTUMU
# --------------------------------------------------

def find_today_heading(full_text):

    today = datetime.today()

    weekday = today.strftime(
        "%A"
    )

    if weekday not in DAYS:

        return None

    day_name = DAYS[
        weekday
    ]

    # --------------------------------------------------
    # U Krba môže mať dátum rôzne zápisy:
    #
    # Utorok 18.8.2026
    # Utorok 18 .8.2026
    # Utorok 18.8 .2026
    # Utorok 18 . 8 . 2026
    #
    # ale dokonca:
    #
    # Utorok 18.8 .202 6
    #
    # Preto povoľujeme medzery aj MEDZI ČÍSLICAMI.
    #
    # Stále však kontrolujeme presný:
    # deň + mesiac + rok.
    # --------------------------------------------------

    day_pattern = "".join(
        rf"{re.escape(digit)}\s*"
        for digit in str(today.day)
    )

    month_pattern = "".join(
        rf"{re.escape(digit)}\s*"
        for digit in str(today.month)
    )

    year_pattern = "".join(
        rf"{re.escape(digit)}\s*"
        for digit in str(today.year)
    )

    pattern = re.compile(

        rf"{re.escape(day_name)}"
        rf"\s+"
        rf"{day_pattern}"
        rf"\s*"
        rf"\."
        rf"\s*"
        rf"{month_pattern}"
        rf"\s*"
        rf"\."
        rf"\s*"
        rf"{year_pattern}",

        re.IGNORECASE
    )

    match = pattern.search(
        full_text
    )

    if match:

        return match

    return None


# --------------------------------------------------
# NÁJDENIE ĎALŠIEHO DŇA
# --------------------------------------------------

def find_next_day_heading(
    full_text,
    start
):

    # --------------------------------------------------
    # Rovnaká tolerancia ako pri dnešnom dátume.
    #
    # Príklady:
    #
    # Streda 19.8.2026
    # Streda 19 .8 .2026
    # Streda 19.8 .202 6
    # --------------------------------------------------

    day_names = (
        "Pondelok|"
        "Utorok|"
        "Streda|"
        "Štvrtok|"
        "Piatok"
    )

    next_day_pattern = re.compile(

        rf"({day_names})"
        rf"\s+"
        rf"\d\s*\d?"
        rf"\s*"
        rf"\."
        rf"\s*"
        rf"\d\s*\d?"
        rf"\s*"
        rf"\."
        rf"\s*"
        rf"\d\s*\d\s*\d\s*\d",

        re.IGNORECASE
    )

    return next_day_pattern.search(
        full_text,
        start
    )


# --------------------------------------------------
# DNEŠNÝ BLOK
# --------------------------------------------------

def find_today_block(full_text):

    today_match = find_today_heading(
        full_text
    )

    if not today_match:

        return None

    start = today_match.end()

    next_match = find_next_day_heading(
        full_text,
        start
    )

    if next_match:

        end = next_match.start()

    else:

        end = len(full_text)

    return full_text[
        start:end
    ]


# --------------------------------------------------
# POLIEVKA
# --------------------------------------------------

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


# --------------------------------------------------
# MENU 1-3
# --------------------------------------------------

def parse_today_meals(today_text):

    meals = []

    # --------------------------------------------------
    # odstránime polievku
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
    # DEZERT NESMIE SPADNÚŤ DO MENU 1-3
    # --------------------------------------------------

    dessert_match = re.search(

        r"\bDezert\s*:",

        meals_text,

        re.IGNORECASE
    )

    if dessert_match:

        meals_text = meals_text[
            :dessert_match.start()
        ]

    # --------------------------------------------------
    # začiatky menu podľa gramáže
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
    # maximálne 3 denné menu
    # --------------------------------------------------

    meals = meals[:3]

    return meals


# --------------------------------------------------
# PARSOVANIE JEDLA
# --------------------------------------------------

def parse_meal_text(
    text,
    number
):

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


# --------------------------------------------------
# DEZERT
# --------------------------------------------------

def parse_dessert(today_text):

    # --------------------------------------------------
    # nájdeme začiatok dezertu
    # --------------------------------------------------

    dessert_match = re.search(

        r"\bDezert\s*:\s*",

        today_text,

        re.IGNORECASE
    )

    # Dezert dnes neexistuje.
    #
    # V takom prípade ho vôbec nepridáme
    # do výsledného JSON.

    if not dessert_match:

        return None

    start = dessert_match.end()

    # --------------------------------------------------
    # hľadáme cenu dezertu
    #
    # napr.:
    #
    # 6,50€
    # 6,50 €
    # --------------------------------------------------

    price_match = re.search(

        r"(\d+,\d+)\s*€",

        today_text[start:],

        re.IGNORECASE
    )

    # Ak existuje "Dezert:", ale nemá cenu,
    # nepovažujeme ho za kompletný dezert.
    #
    # Teda nevytvoríme:
    #
    # "dessert": {
    #     "name": "...",
    #     "price": null
    # }
    #
    # ale dezert vôbec nepridáme.

    if not price_match:

        return None

    end = (
        start
        +
        price_match.start()
    )

    dessert_text = clean_text(

        today_text[
            start:end
        ]
    )

    if not dessert_text:

        return None

    # --------------------------------------------------
    # alergény
    # --------------------------------------------------

    allergens = extract_allergens(
        dessert_text
    )

    # --------------------------------------------------
    # názov bez alergénov
    # --------------------------------------------------

    name = remove_allergens(
        dessert_text
    )

    name = clean_text(
        name
    )

    if not name:

        return None

    # --------------------------------------------------
    # cena
    # --------------------------------------------------

    price = (
        price_match.group(1)
        + " €"
    )

    return {

        "name": name,

        "allergens": allergens,

        "price": price
    }


# --------------------------------------------------
# MENU 4-5
# --------------------------------------------------

def parse_extra_menu(
    text,
    number
):

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


# --------------------------------------------------
# HLAVNÝ SCRAPER
# --------------------------------------------------

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
    # POLIEVKA
    # --------------------------------------------------

    soup_data = parse_soup(
        today_text
    )

    # --------------------------------------------------
    # MENU 1-3
    # --------------------------------------------------

    meals = parse_today_meals(
        today_text
    )

    # --------------------------------------------------
    # DEZERT
    # --------------------------------------------------

    dessert = parse_dessert(
        today_text
    )

    # --------------------------------------------------
    # MENU 4-5
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
        # MENU 4
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
        # MENU 5
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

    # --------------------------------------------------
    # základný výsledok
    # --------------------------------------------------

    result = {

        "restaurant": "U Krba",

        "type": "classic_menu",

        "soup": soup_data,

        "meals": meals
    }

    # --------------------------------------------------
    # DEZERT
    #
    # pridáme IBA ak:
    #
    # 1. existuje "Dezert:"
    # 2. má názov
    # 3. má cenu
    #
    # Ak dezert na stránke nebude,
    # kľúč "dessert" sa vôbec nevytvorí.
    # --------------------------------------------------

    if dessert is not None:

        result[
            "dessert"
        ] = dessert

    return result


# --------------------------------------------------
# TEST
# --------------------------------------------------

def main():

    data = scrape_ukrba()

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":

    main()