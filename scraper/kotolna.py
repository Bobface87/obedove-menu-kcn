import re
from datetime import datetime
from io import BytesIO

import pdfplumber
import requests


PDF_URL = "https://starakotolna.sk/wp-content/uploads/2026/07/Obedove-menu-Kotolna-262026.pdf"


DAY_NAMES = [
    "Pondelok",
    "Utorok",
    "Streda",
    "Štvrtok",
    "Piatok",
]


def download_pdf():

    print("⬇ Sťahujem PDF...")

    r = requests.get(
        PDF_URL,
        timeout=20
    )

    r.raise_for_status()

    return BytesIO(r.content)



def load_text():

    pdf_file = download_pdf()

    text = ""

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text



def today_name():

    return DAY_NAMES[datetime.today().weekday()]



def split_days(text):

    pattern = (
        r"Denné menu na "
        r"(?:Pondelok|Utorok|Streda|Štvrtok|Piatok)"
        r".*?"
        r"(?=Denné menu na|\Z)"
    )

    return [
        x.group(0)
        for x in re.finditer(
            pattern,
            text,
            flags=re.S
        )
    ]



def find_today_block(text):

    today = today_name()

    for block in split_days(text):

        if f"Denné menu na {today}" in block:
            return block

    return None



def clean_meal(text):

    # MENU označenie
    text = re.sub(
        r"Menu\s+\d+:",
        "",
        text,
        flags=re.I
    )


    # odstráni alergény v lomkách
    text = re.sub(
        r"/[^/]+/",
        "",
        text
    )


    # odstráni iba SK označenie
    text = re.sub(
        r"\(SK\)",
        "",
        text,
        flags=re.I
    )


    # odstráni cenu donášky aj bez hviezdičiek
    text = re.sub(
        r"\*?Cena pre donášku a osobný odber:.*",
        "",
        text,
        flags=re.I | re.S
    )


    # odstráni ceny
    text = re.sub(
        r"\d+,\d+\s*€",
        "",
        text
    )


    # odstráni hviezdičky
    text = text.replace("*", "")


    text = " ".join(
        text.split()
    )


    return text.strip()



def extract_price(text):

    prices = re.findall(
        r"\d+,\d+\s*€",
        text
    )

    if prices:

        return float(
            prices[0]
            .replace(",", ".")
            .replace("€", "")
        )

    return None



def parse_today(block):

    soup = ""

    meals = []


    soup_match = re.search(
        r"Polievka:(.*?)(?=Menu 1:)",
        block,
        flags=re.S
    )


    if soup_match:

        soup = clean_meal(
            soup_match.group(1)
        )


    for i in range(1,7):

        pattern = (
            rf"Menu {i}:"
            r"(.*?)"
            rf"(?=Menu {i+1}:|Jedálny lístok|\Z)"
        )


        result = re.search(
            pattern,
            block,
            flags=re.S
        )


        if not result:
            continue


        raw = result.group(1)


        meals.append(
            {
                "name": clean_meal(raw),
                "price": extract_price(raw)
            }
        )


    return soup, meals



def scrape_kotolna():

    print("Načítavam Kotolňu...")

    text = load_text()

    block = find_today_block(text)


    if not block:

        raise Exception(
            "Dnešný deň sa nenašiel"
        )


    soup, meals = parse_today(block)


    return {
        "restaurant": "Kotolňa",
        "soup": soup,
        "meals": meals
    }



if __name__ == "__main__":

    data = scrape_kotolna()

    print(data)