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

    r = requests.get(PDF_URL, timeout=20)
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
        m.group(0)
        for m in re.finditer(
            pattern,
            text,
            flags=re.S
        )
    ]


def find_today_block(text):

    today = today_name()

    blocks = split_days(text)

    for block in blocks:

        if f"Denné menu na {today}" in block:
            return block

    return None


def clean_meal(text):

    text = re.sub(
        r"Menu\s+\d+:",
        "",
        text
    )

    text = re.sub(
        r"^\d+\s*g\s*",
        "",
        text
    )

    text = re.sub(
        r"\([^)]*SK[^)]*\)",
        "",
        text
    )

    text = re.sub(
        r"/[^/]+/",
        "",
        text
    )

    text = re.sub(
        r"\*Cena pre donášku.*",
        "",
        text,
        flags=re.S
    )

    text = re.sub(
        r"\d+,\d+\s*€",
        "",
        text
    )

    text = " ".join(
        text.split()
    )

    return text.strip()


def extract_price(text):

    prices = re.findall(
        r"\d+,\d+\s*€",
        text
    )

    if not prices:
        return None

    return prices[0]


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


    for i in range(1, 7):

        pattern = (
            rf"Menu {i}:"
            r"(.*?)"
            rf"(?=Menu {i+1}:|Jedálny lístok|\Z)"
        )

        match = re.search(
            pattern,
            block,
            flags=re.S
        )


        if not match:
            continue


        raw = match.group(1)


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

        print("❌ Dnešný deň sa nenašiel")

        return {
            "restaurant": "Kotolňa",
            "soup": "",
            "meals": []
        }


    soup, meals = parse_today(block)


    return {
        "restaurant": "Kotolňa",
        "soup": soup,
        "meals": meals
    }



def main():

    data = scrape_kotolna()


    print()
    print(data["restaurant"])

    print()
    print("POLIEVKA:")
    print(data["soup"])

    print()


    for index, meal in enumerate(
        data["meals"],
        start=1
    ):

        print(
            "MENU",
            index
        )

        print(
            meal["name"]
        )

        print(
            "Cena:",
            meal["price"]
        )

        print("-" * 50)



if __name__ == "__main__":
    main()