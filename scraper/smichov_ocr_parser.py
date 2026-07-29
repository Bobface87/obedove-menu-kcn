import re


DAY_NAMES = [
    "pondelok",
    "utorok",
    "streda",
    "štvrtok",
    "piatok"
]


def normalize_text(text):

    text = text.replace("\r", "")
    text = text.replace("€", " €")

    return text



def clean_soup_text(text):

    if not text:
        return ""


    text = text.strip()


    replacements = {

        "0,3!": "0,3l",

        "0,31": "0,3l",

        "0,3I": "0,3l",

        "0,3|": "0,3l",

    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    return text



def find_current_day_block(text):

    text_lower = text.lower()

    positions = []

    for day in DAY_NAMES:

        pos = text_lower.find(day)

        if pos != -1:

            positions.append(
                (pos, day)
            )


    if not positions:

        return ""


    positions.sort()


    start = positions[0][0]

    end = len(text)


    for pos, _ in positions:

        if pos > start:

            end = pos

            break


    return text[start:end]



def extract_soup(block):

    match = re.search(
        r"Polievka:\s*(.*?)(?=\nMenu|\n\n|$)",
        block,
        re.IGNORECASE | re.DOTALL
    )


    if not match:

        return ""


    soup = (

        match.group(1)

        .replace("\n", " ")

        .strip()

    )


    if len(soup) < 5:

        return ""


    return clean_soup_text(
        soup
    )



def extract_extra_soup(text):

    match = re.search(

        r"Polievka v ponuke každý deň:\s*.*?Polievka:\s*(.*?)(?=\n\n|A alergénov|$)",

        text,

        re.IGNORECASE | re.DOTALL

    )


    if not match:

        return ""


    soup = (

        match.group(1)

        .replace("\n", " ")

        .strip()

    )


    if len(soup) < 5:

        return ""


    return clean_soup_text(
        soup
    )



def extract_menu(block, number):

    match = re.search(

        rf"Menu\s*{number}\s*:\s*(.*?)(?=\nMenu|\n\n|$)",

        block,

        re.IGNORECASE | re.DOTALL

    )


    if not match:

        return None


    line = (

        match.group(1)

        .replace("\n", " ")

        .strip()

    )


    price_match = re.search(

        r"(\d+,\d+)\s*€",

        line

    )


    price = ""


    if price_match:

        price = (

            price_match.group(1)

            + " €"

        )


        line = (

            line[:price_match.start()]

            .strip()

        )


    return {

        "name": f"MENU {number}",

        "description": line,

        "price": price

    }



def extract_daily_menus(block):

    meals = []


    for number in (1, 2):

        menu = extract_menu(

            block,

            number

        )


        if menu:

            meals.append(
                menu
            )


    return meals



def extract_permanent_menus(text):

    meals = []


    for number in (3, 4):

        match = re.search(

            rf"Menu\s*{number}\s*:\s*(.*?)(?=\nMenu|\nPolievka v ponuke|$)",

            text,

            re.IGNORECASE | re.DOTALL

        )


        if not match:

            continue


        line = (

            match.group(1)

            .replace("\n", " ")

            .strip()

        )


        price_match = re.search(

            r"(\d+,\d+)\s*€",

            line

        )


        price = ""


        if price_match:

            price = (

                price_match.group(1)

                + " €"

            )


            line = (

                line[:price_match.start()]

                .strip()

            )


        meals.append(

            {

                "name": f"MENU {number}",

                "description": line,

                "price": price

            }

        )


    return meals



def parse_smichov_menu(text):

    text = normalize_text(
        text
    )


    day_block = find_current_day_block(
        text
    )


    soup = extract_soup(
        day_block
    )


    extra_soup = extract_extra_soup(
        text
    )


    meals = []


    meals.extend(

        extract_daily_menus(
            day_block
        )

    )


    meals.extend(

        extract_permanent_menus(
            text
        )

    )


    return {

        "restaurant": "Smíchov",

        "type": "ocr_menu",

        "soup": soup,

        "meals": meals,

        "extra_soup": extra_soup

    }