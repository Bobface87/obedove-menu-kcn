import re
import json
from datetime import datetime
from io import BytesIO

import requests
import pdfplumber
from bs4 import BeautifulSoup


# =====================================================
# SETTINGS
# =====================================================

MAIN_URL = "https://sakura1.eatbu.com/?lang=sk#"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 Windows NT 10.0 "
        "Chrome/137 Safari/537.36"
    )
}


DAY_CODES = {
    0: "PO",
    1: "UT",
    2: "ST",
    3: "ŠT",
    4: "PI",
}



# =====================================================
# DAY
# =====================================================

def today_code():

    d = datetime.today().weekday()


    if d > 4:

        raise Exception(
            "Sakura cez víkend menu nemá"
        )


    return DAY_CODES[d]



# =====================================================
# FIND PDF
# =====================================================

def get_pdf_url():

    r = requests.get(
        MAIN_URL,
        headers=HEADERS,
        timeout=20
    )

    r.raise_for_status()


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    pdfs = []


    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]


        if ".pdf" in href.lower():

            if href not in pdfs:

                pdfs.append(
                    href
                )



    if len(pdfs) < 5:

        raise Exception(
            "Nenašlo sa 5 denných PDF menu"
        )



    day = datetime.today().weekday()



    if day > 4:

        raise Exception(
            "Sakura cez víkend menu nemá"
        )


    return pdfs[day]



# =====================================================
# DOWNLOAD PDF
# =====================================================

def download_pdf():

    url = get_pdf_url()


    r = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )


    r.raise_for_status()


    return BytesIO(
        r.content
    )



# =====================================================
# EXTRACT PDF COLUMNS
# =====================================================


def build_column(words):


    words = sorted(
        words,
        key=lambda x: (
            x["top"],
            x["x0"]
        )
    )



    lines = []

    current = []

    last_y = None



    for w in words:


        y = w["top"]



        if (
            last_y is None
            or abs(y-last_y) < 5
        ):


            current.append(
                w["text"]
            )



        else:


            lines.append(
                " ".join(current)
            )


            current = [
                w["text"]
            ]



        last_y = y



    if current:

        lines.append(
            " ".join(current)
        )



    return lines





def extract_columns():


    pdf = download_pdf()



    with pdfplumber.open(pdf) as doc:


        page = doc.pages[0]


        words = page.extract_words()



        left = []

        right = []



        for w in words:


            if w["x0"] < 300:

                left.append(w)


            else:

                right.append(w)



        return (

            build_column(left),

            build_column(right)

        )

# =====================================================
# HELPERS
# =====================================================


def remove_leading_price(line):

    return re.sub(
        r"^\s*\d+,\d{2}\s*€\s*",
        "",
        line
    ).strip()





def has_price(line):

    return bool(
        re.search(
            r"\d+,\d{2}\s*€",
            line
        )
    )





def has_weight(line):

    return bool(
        re.search(
            r"\d+\s*(g|ks|l)",
            line,
            re.I
        )
    )





def only_weight(line):

    return bool(
        re.fullmatch(
            r"\d+\s*(g|ks|l)",
            line.strip(),
            re.I
        )
    )





def has_menu_number(line):

    clean = remove_leading_price(line)


    return bool(
        re.match(
            r"^\d+\.|^[A-D]\.",
            clean
        )
    )





def is_variant(line):

    return bool(
        re.search(
            r"(^|\s)[a-c]\)",
            line,
            re.I
        )
    )





def has_allergen(line):

    return (
        "/" in line
        and
        bool(
            re.search(
                r"\d",
                line
            )
        )
    )





def is_section(line):

    return line.upper().strip() in [

        "POLIEVKY",

        "SUSHI",

        "TÝŽDENNÁ PONUKA",

        "TEPLÉ JEDLÁ"

    ]





# =====================================================
# DESCRIPTION DETECTOR
# =====================================================


def looks_like_description(line):


    if not line.strip():

        return False



    if has_price(line):

        return False



    if has_menu_number(line):

        return False



    if is_section(line):

        return False



    forbidden = [

        "OBEDOVÉ MENU",

        "PRIPRAVENÚ NAŠU TÝŽDENNÚ PONUKU",

        "VYCHUTNAŤ PON",

        "NEVYBRALI STE SI"

    ]



    upper = line.upper()



    for x in forbidden:

        if x in upper:

            return False



    return True





# =====================================================
# ITEM DETECTOR
# =====================================================


def parse(lines):


    output = []


    current = False


    main_amount = None



    for index,line in enumerate(lines):



        if is_section(line):


            output.append(

                (
                    "SECTION",
                    line
                )

            )


            current = False

            main_amount = None


            continue





        # ---------------------------------------------
        # VARIANTY
        # ---------------------------------------------


        if current and is_variant(line):


            output.append(

                (
                    "ITEM CONTINUE",
                    line,
                    "VARIANT"
                )

            )


            continue





        # ---------------------------------------------
        # SAMOSTATNA GRAMAZ
        # ---------------------------------------------


        if current and only_weight(line):


            output.append(

                (
                    "ITEM CONTINUE",
                    line,
                    "WEIGHT"
                )

            )


            continue





        # ---------------------------------------------
        # SCORE
        # ---------------------------------------------


        clean = remove_leading_price(line)


        score = 0


        reasons = []



        if has_menu_number(line):

            score += 50

            reasons.append(
                "MENU"
            )



        if has_weight(line):

            score += 20

            reasons.append(
                "WEIGHT"
            )



        if has_price(line):

            score += 20

            reasons.append(
                "PRICE"
            )



        if len(clean) > 8:

            score += 10

            reasons.append(
                "NAME"
            )





        # ---------------------------------------------
        # POLIEVKY
        # ---------------------------------------------


        if index <= 6:


            soup_candidate = (

                len(clean) > 5

                and

                (
                    has_price(line)

                    or

                    has_weight(line)
                )

            )



            if soup_candidate:


                score = 100


                reasons = [

                    "SOUP"

                ]





        # ---------------------------------------------
        # START ITEM
        # ---------------------------------------------

            # sushi skladba - napr. 8ks uramaki, 3ks maki
            # nikdy nezačína nový item

            if current and re.match(
                r"^\d+\s*ks\b",
                line,
                re.I
            ):
                output.append(
                    (
                        "DESCRIPTION",
                        line
                    )
                )

                continue

        if score >= 60 and not is_variant(line):


            current = True



            m = re.search(

                r"(\d+)\s*(g|ks|l)",

                line

            )



            if m:


                main_amount = int(

                    m.group(1)

                )



            output.append(

                (
                    "ITEM START",
                    line,
                    reasons
                )

            )


            continue        


        # ---------------------------------------------
        # CONTINUE ITEM
        # ---------------------------------------------


        if current:


            # -----------------------------------------
            # ALERGÉNY
            # -----------------------------------------


            if has_allergen(line):


                output.append(

                    (
                        "ITEM CONTINUE",
                        line,
                        "ALLERGEN"
                    )

                )


                continue





            # -----------------------------------------
            # SAMOSTATNÁ CENA
            # -----------------------------------------


            if re.fullmatch(

                r"\d+,\d{2}\s*€",

                line.strip()

            ):


                output.append(

                    (
                        "ITEM CONTINUE",
                        line,
                        "PRICE"
                    )

                )


                continue





            # -----------------------------------------
            # MENŠIA GRAMÁŽ = POPIS
            # napr. hlavné jedlo 250g
            # popis mäso 120g
            # -----------------------------------------


            m = re.search(

                r"(\d+)\s*(g|ks|l)",

                line

            )



            if m and main_amount:



                if int(m.group(1)) < main_amount:



                    output.append(

                        (
                            "DESCRIPTION",
                            line
                        )

                    )


                    continue





            # -----------------------------------------
            # DESCRIPTION
            # -----------------------------------------


            if looks_like_description(line):


                output.append(

                    (
                        "DESCRIPTION",
                        line
                    )

                )


                continue





            # -----------------------------------------
            # KONIEC ITEMU
            # -----------------------------------------


            output.append(

                (
                    "NORMAL",
                    line
                )

            )


            current = False

            main_amount = None


            continue





        # ---------------------------------------------
        # MIMO ITEMU
        # ---------------------------------------------


        output.append(

            (
                "NORMAL",
                line
            )

        )



    return output







# =====================================================
# ITEM ATTRIBUTE ANALYZER
# =====================================================


def analyze_attributes(text):


    result = {


        "number": None,

        "name": None,

        "weight": None,

        "price": None,

        "allergens": None


    }



    original = text





    # ---------------------------------------------
    # NUMBER
    # ---------------------------------------------


    m = re.search(

        r"^\s*(\d+\.|[A-D]\.)",

        text

    )



    if m:


        result["number"] = (

            m.group(1)

            .replace(".", "")

        )



        text = text[

            m.end():

        ].strip()





    # ---------------------------------------------
    # PRICE
    # ---------------------------------------------


    m = re.search(

        r"(\d+\s*,\s*\d{2})\s*€",

        text

    )



    if m:


        result["price"] = m.group()



        text = text.replace(

            m.group(),

            ""

        ).strip()



        result["price"] = (
            result["price"]
            .replace(" ", "")
        )


        # -----------------------------------------
        # NUMBER ZA CENOU
        # napr.
        # 7,05 € B. KURACIE KÚSKY
        # -----------------------------------------


        if result["number"] is None:


            m = re.search(

                r"^\s*(\d+\.|[A-D]\.)",

                text

            )


            if m:


                result["number"] = (

                    m.group(1)

                    .replace(".", "")

                )


                text = text[

                    m.end():

                ].strip()





    # ---------------------------------------------
    # WEIGHT
    # ---------------------------------------------


    m = re.search(

        r"\d+(?:,\d+)?\s*(g|ks|l)",

        text,

        re.I

    )



    if m:


        result["weight"] = m.group()



        text = text.replace(

            m.group(),

            ""

        ).strip()





    text = re.sub(

        r"\s+\d+$",

        "",

        text

    ).strip()





    # ---------------------------------------------
    # ALLERGEN
    # ---------------------------------------------


    m = re.search(

        r"/(.+?)/",

        text

    )



    if m:


        result["allergens"] = (

            m.group(1)

            .strip()

        )



        text = text.replace(

            m.group(),

            ""

        ).strip()





    # ---------------------------------------------
    # VARIANT
    # ---------------------------------------------


    if re.search(

        r"(^|\s)[a-c]\)",

        original,

        re.I

    ):


        result["variant"] = True


    else:


        result["variant"] = False





    text = re.sub(

        r"\(\s*\)",

        "",

        text

    ).strip()


    # odstránenie zvyšnej ceny z názvu variantu

    text = re.sub(
        r"\d+\s*,\s*\d{2}\s*€",
        "",
        text
    ).strip()



    # ---------------------------------------------
    # NAME
    # ---------------------------------------------


    if text:


        result["name"] = text





    return result



# =====================================================
# CLEAN ITEM
# =====================================================


def clean_item(item):


    if item.get("name"):


        item["name"] = re.sub(

            r"\s+",

            " ",

            item["name"]

        ).strip()





    if item.get("allergens"):


        item["allergens"] = re.sub(

            r"\s+",

            "",

            item["allergens"]

        )





    if item.get("price"):

        item["price"] = re.sub(
            r"\s*€",
            " €",
            item["price"]
        )





    if item.get("weight"):


        item["weight"] = re.sub(

            r"\s+",

            "",

            item["weight"]

        )



    return item







# =====================================================
# BUILD MENU
# =====================================================


def build_menu(parsed_rows):


    menu = []


    current_item = None


    description_parts = []





    for row in parsed_rows:


        row_type = row[0]





        # -----------------------------------------
        # NORMAL ignorujeme
        # -----------------------------------------


        if row_type == "NORMAL":

            continue





        # -----------------------------------------
        # ITEM START
        # -----------------------------------------


        if row_type == "ITEM START":



            if current_item:



                if description_parts:


                    current_item["description"] = (

                        " ".join(

                            description_parts

                        )

                    )



                menu.append(

                    current_item

                )





            attr = analyze_attributes(

                row[1]

            )





            current_item = clean_item({


                "number": attr["number"],


                "name": attr["name"],


                "weight": attr["weight"],


                "price": attr["price"],


                "allergens": attr["allergens"],


                "variants": [],


                "description": ""

            })



            description_parts = []



            continue





        # -----------------------------------------
        # ITEM CONTINUE
        # -----------------------------------------


        if row_type == "ITEM CONTINUE" and current_item:



            attr = analyze_attributes(

                row[1]

            )



            reason = row[2]





            if reason == "ALLERGEN":


                current_item["allergens"] = (

                    attr["allergens"]

                )





            elif reason == "WEIGHT":


                current_item["weight"] = (

                    attr["weight"]

                )





            elif reason == "PRICE":


                current_item["price"] = (

                    attr["price"]

                )





            elif reason == "VARIANT":


                variant = {


                    "name": attr["name"],


                    "weight": attr["weight"],


                    "price": attr["price"]


                }


                variant = clean_item(
                    variant
                )


                current_item["variants"].append(
                    variant
                )



            continue





        # -----------------------------------------
        # DESCRIPTION
        # -----------------------------------------


        if row_type == "DESCRIPTION" and current_item:



            description_parts.append(

                row[1]

            )


            continue







    # ---------------------------------------------
    # posledný item
    # ---------------------------------------------


    if current_item:



        if description_parts:


            current_item["description"] = (

                " ".join(

                    description_parts

                )

            )



        menu.append(

            current_item

        )





    return menu







# =====================================================
# HLAVNÁ SCRAPE FUNKCIA
# =====================================================


def scrape_sakura():


    print(

        "Načítavam Sakuru..."

    )



    left, right = extract_columns()





    parsed_left = parse(left)

    parsed_right = parse(right)


    menu = []

    menu.extend(
        build_menu(parsed_left)
    )

    menu.extend(
        build_menu(parsed_right)
    )





    return {


        "restaurant": "Sakura",


        "daily_menu": menu


    }




# =====================================================
# TEST
# =====================================================


if __name__ == "__main__":


    data = scrape_sakura()



    print(

        json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        )

    )