import re


MENU_HEADERS = [
    "CLASSIC MENU",
    "DAILY CHOICE MENU",
    "FIT MENU",
    "BUSINESS MENU",
]


REMOVE_TEXT_PATTERNS = [
    r"OBEDOVÉ MENU SA PREDÁVA DO VYPREDANIA ZÁSOB\.?",
    r"ZMENA PRÍLOHY MENU SA ÚČTUJE.*",
]


def normalize_price(price):
    """
    Oprava typických OCR chýb pri cenách.
    """

    if not price:
        return None

    price = price.replace(
        " ",
        ""
    )


    if price in [
        "1,50€",
        "1,90€",
        "1,30€",
        "1,40€"
    ]:
        return None


    match = re.match(
        r"(\d+,\d+)€",
        price
    )


    if match:

        return (
            match.group(1)
            + " €"
        )


    return price



def extract_price(text):

    match = re.search(
        r"(\d+,\d+)\s*€",
        text
    )


    if match:

        return normalize_price(
            match.group(1) + "€"
        )


    return None



def clean_name(text):

    text = text.replace(
        "-",
        " - "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



def clean_text(text):

    for pattern in REMOVE_TEXT_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )


    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()



def is_menu_header(line):

    upper = line.upper()

    for header in MENU_HEADERS:

        if header in upper:
            return True

    return False



def parse_menu_text(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


    meals = []

    current = None


    for line in lines:


        if is_menu_header(line):

            if current:
                meals.append(current)


            current = {

                "name": clean_name(line),

                "description": "",

                "price": None

            }

            continue



        if current:


            price = extract_price(line)


            if price:

                current["price"] = price


                line = re.sub(
                    r"\d+,\d+\s*€",
                    "",
                    line
                ).strip()



            if line:

                current["description"] += (
                    " " + line
                )



    if current:

        meals.append(current)



    for meal in meals:

        meal["description"] = clean_text(
            meal["description"]
        )


    return meals