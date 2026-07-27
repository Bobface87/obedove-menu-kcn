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
    Oprava OCR cien.
    """

    if not price:
        return None

    price = price.replace(" ", "")

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
        return match.group(1) + " €"

    return None



def extract_price(text):

    prices = re.findall(
        r"(\d+,\d+)\s*€",
        text
    )

    if not prices:
        return None


    for price in reversed(prices):

        result = normalize_price(
            price + "€"
        )

        if result:
            return result


    return None



def clean_text(text):

    for pattern in REMOVE_TEXT_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )


    text = re.sub(
        r"/zmena menu polievky.*",
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



def is_menu_header(line):

    upper = line.upper()

    return any(
        header in upper
        for header in MENU_HEADERS
    )



def parse_menu_text(text):


    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


    result = {

        "starter": "",

        "soup": "",

        "meals": []

    }



    # =========================
    # PREDJEDLO
    # =========================

    starter_start = None
    soup_start = None


    for i, line in enumerate(lines):

        upper = line.upper().strip()


        if "PREDJEDLO" in upper:

            starter_start = i



        # iba samostatná POLIEVKA
        if upper == "POLIEVKA":

            soup_start = i



    if starter_start is not None and soup_start is not None:

        starter_lines = lines[
            starter_start + 1:soup_start
        ]


        result["starter"] = clean_text(
            " ".join(starter_lines)
        )



    # =========================
    # POLIEVKA
    # =========================

    soup_lines = []


    if soup_start is not None:


        for line in lines[soup_start + 1:]:


            if is_menu_header(line):

                break


            soup_lines.append(line)



    soup_text = " ".join(
        soup_lines
    )


    # OCR opravy objemu

    soup_text = re.sub(
        r"0,251",
        "0,25 l",
        soup_text,
        flags=re.IGNORECASE
    )


    soup_text = re.sub(
        r"0,25l",
        "0,25 l",
        soup_text,
        flags=re.IGNORECASE
    )


    soup_text = re.sub(
        r"0,25[iI]",
        "0,25 l",
        soup_text,
        flags=re.IGNORECASE
    )


    result["soup"] = clean_text(
        soup_text
    )



    # =========================
    # MENU
    # =========================

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



    result["meals"] = meals


    return result