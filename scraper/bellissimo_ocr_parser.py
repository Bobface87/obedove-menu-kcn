import re
import unicodedata

from datetime import datetime


DAYS = [
    "Pondelok",
    "Utorok",
    "Streda",
    "Štvrtok",
    "Piatok"
]


# ==================================================
# Pomocné funkcie
# ==================================================

def remove_diacritics(text):

    return "".join(
        c
        for c in unicodedata.normalize(
            "NFD",
            text
        )
        if unicodedata.category(c) != "Mn"
    )



def today_name():

    weekday = datetime.now().weekday()

    if weekday < 5:
        return DAYS[weekday]

    return "Pondelok"



def clean_text(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



# ==================================================
# OCR opravy
# ==================================================

def fix_price_errors(text):

    replacements = {

        "9920€": "9,90€",
        "990€": "9,90€",
        "1090€": "10,90€",
        "890€": "8,90€",
        "1690€": "16,90€",

        "10.90€": "10,90€",

    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    return text



def fix_grammage_errors(text):

    replacements = {

        "3809": "380g",
        "3509": "350g",
        "5509": "550g",

        "SOg": "50g",
        "S0g": "50g",

        "l60a": "160g",
        "l60g": "160g",

        "i50g": "150g",


        # --------------------------
        # Polievka ml OCR opravy
        # --------------------------

        "Z00nnl": "300ml",
        "Z00ml": "300ml",
        "300m1": "300ml",
        "3001m": "300ml",


    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    return text



def fix_common_ocr_words(text):

    replacements = {

        "BBO": "BBQ",
        "teriyvaki": "teriyaki",
        "steriyaki": "teriyaki",
        "snitake": "shitake",
        "chery": "cherry",


        # --------------------------
        # Zátvorky OCR
        # --------------------------

        "(1,7]": "(1,7)",

    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    return text



def clean_ocr_errors(text):

    text = fix_grammage_errors(
        text
    )

    text = fix_price_errors(
        text
    )

    text = fix_common_ocr_words(
        text
    )

    return text



# ==================================================
# Čísla menu
# ==================================================

def normalize_menu_number(text):

    replacements = {

        "S.": "5.",
        "S,": "5,",
        "s.": "5.",
        "s,": "5,",

    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    text = re.sub(
        r"^(\d+)[,](?=\s)",
        r"\1.",
        text
    )


    text = re.sub(
        r"^(\d+)\.(?=\d)",
        r"\1. ",
        text
    )


    return text



# ==================================================
# Cena
# ==================================================

def extract_price(text):

    text = fix_price_errors(
        text
    )


    matches = re.findall(
        r"(\d{1,2}[.,]\d{2})\s*€?",
        text
    )


    if matches:

        price = matches[-1]

        price = price.replace(
            ".",
            ","
        )

        return price + " €"



    partial = re.findall(
        r"(\d{1,2}),$",
        text.strip()
    )


    if partial:

        return partial[-1] + ",90 €"



    return None



def remove_price(text):

    text = fix_price_errors(
        text
    )


    text = re.sub(
        r"\d{1,2}[.,]\d{2}\s*€?",
        "",
        text
    )


    text = re.sub(
        r"\d{1,2},$",
        "",
        text
    )


    return text



# ==================================================
# Dni
# ==================================================

def find_day_block(text, day):

    lines = [

        line.strip()

        for line in text.splitlines()

        if line.strip()

    ]


    start = None


    wanted = remove_diacritics(
        day.lower()
    )


    for i, line in enumerate(lines):

        check = remove_diacritics(
            line.lower()
        )


        if check.startswith(
            wanted
        ):

            start = i
            break



    if start is None:

        return []



    end = len(lines)



    for i in range(start + 1, len(lines)):

        current = remove_diacritics(
            lines[i].lower()
        )


        for next_day in DAYS:

            if current.startswith(
                remove_diacritics(
                    next_day.lower()
                )
            ):

                end = i
                break


        if end != len(lines):

            break



    return lines[start:end]



# ==================================================
# Polievka
# ==================================================

def looks_like_soup(text):

    check = remove_diacritics(
        text.lower()
    )


    # náhradná týždenná polievka - ignorujeme

    if "slepa" in check and "rezanc" in check:

        return False



    keywords = [

        "poliev",
        "krem",
        "kapust",
        "kysla",
        "slepa",
        "zelenin",
        "brokolic",
        "zemiak"

    ]


    return any(
        word in check
        for word in keywords
    )



# ==================================================
# Parser
# ==================================================

def parse_bellissimo_menu(text, day=None):


    if day is None:

        day = today_name()



    lines = find_day_block(
        text,
        day
    )



    result = {

        "starter": "",

        "soup": "",

        "meals": []

    }



    if len(lines) < 2:

        return result



    content = lines[1:]



    # --------------------------
    # POLIEVKA
    # --------------------------

    soup_index = None


    for i, line in enumerate(content[:3]):

        if looks_like_soup(line):

            soup_index = i

            break



    if soup_index is not None:

        result["soup"] = clean_text(
            clean_ocr_errors(
                content[soup_index]
            )
        )

        content.pop(
            soup_index
        )



    # --------------------------
    # MENU
    # --------------------------

    menu_blocks = []

    current = None



    for line in content:


        line = normalize_menu_number(
            line
        )


        match = re.match(
            r"^([1-5])\.\s*(.*)",
            line
        )



        if match:


            if current:

                menu_blocks.append(
                    current
                )



            current = {

                "number": match.group(1),

                "text": match.group(2)

            }



        else:


            if current:

                current["text"] += (
                    " " + line
                )



    if current:

        menu_blocks.append(
            current
        )



    # --------------------------
    # OCHRANA MENU 5
    # --------------------------

    has_tagliata = any(

        "tagliata" in item["text"].lower()

        for item in menu_blocks

    )


    if has_tagliata and not any(

        item["number"] == "5"

        for item in menu_blocks

    ):

        for item in menu_blocks:

            if "tagliata" in item["text"].lower():

                item["number"] = "5"



    meals = []



    for item in menu_blocks:


        value = clean_ocr_errors(
            item["text"]
        )


        price = extract_price(
            value
        )


        description = remove_price(
            value
        )



        meals.append({

            "name": "MENU " + item["number"],

            "description": clean_text(
                description
            ),

            "price": price

        })



    result["meals"] = meals



    return result