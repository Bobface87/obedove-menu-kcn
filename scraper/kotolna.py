import re
from datetime import datetime
from io import BytesIO

import pdfplumber
import requests
from bs4 import BeautifulSoup


MAIN_URL = "https://starakotolna.sk/"


DAY_NAMES = [
    "Pondelok",
    "Utorok",
    "Streda",
    "Štvrtok",
    "Piatok",
]


def get_pdf_url():

    print("🔎 Hľadám aktuálne PDF menu...")

    r = requests.get(
        MAIN_URL,
        timeout=20
    )

    r.raise_for_status()


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link["href"]

        text = link.get_text(
            " ",
            strip=True
        ).lower()


        if ".pdf" in href.lower():

            if (
                "menu" in text
                or "obed" in text
                or "menu" in href.lower()
                or "obed" in href.lower()
            ):

                if href.startswith("/"):

                    href = (
                        "https://starakotolna.sk"
                        + href
                    )


                return href


    raise Exception(
        "Aktuálne PDF obedového menu sa nenašlo"
    )



def download_pdf():

    print("⬇ Sťahujem PDF...")


    pdf_url = get_pdf_url()


    print(
        "PDF URL:",
        pdf_url
    )


    r = requests.get(
        pdf_url,
        timeout=20
    )


    r.raise_for_status()


    return BytesIO(
        r.content
    )



def load_text():

    pdf_file = download_pdf()

    text = ""


    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            t = page.extract_text()

            if t:

                text += t + "\n"


    return text



def today_name():

    return DAY_NAMES[
        datetime.today().weekday()
    ]



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



def extract_price(text):

    prices = re.findall(
        r"\d+,\d+\s*€",
        text
    )


    if prices:

        return prices[0]


    return None



def remove_delivery_text(text):

    # odstráni všetko od "Cena pre" až po koniec donáškového textu

    text = re.sub(
        r"Cena\s+pre.*?(?=\d+,\d+\s*€)",
        "",
        text,
        flags=re.I | re.S
    )


    text = re.sub(
        r"donášku.*?(?=\d+,\d+\s*€)",
        "",
        text,
        flags=re.I | re.S
    )


    text = re.sub(
        r"osobný.*?(?=\d+,\d+\s*€)",
        "",
        text,
        flags=re.I | re.S
    )


    return text



def clean_meal(text):

    # spojenie zalomených riadkov PDF

    text = " ".join(
        text.split()
    )


    # odstráni menu číslo

    text = re.sub(
        r"Menu\s+\d+:",
        "",
        text
    )


    # odstráni donášku

    text = remove_delivery_text(
        text
    )


    # odstráni alergény

    text = re.sub(
        r"/[^/]+/",
        "",
        text
    )


    # odstráni SK

    text = re.sub(
        r"\(SK\)",
        "",
        text,
        flags=re.I
    )


    # odstráni gramáž

    text = re.sub(
        r"^\d+\s*g\s*",
        "",
        text
    )


    # odstráni ceny

    text = re.sub(
        r"\d+,\d+\s*€",
        "",
        text
    )


    # odstráni hviezdičky

    text = text.replace(
        "*",
        ""
    )


    # odstráni zvyšné kúsky footeru PDF

    text = re.sub(
        r"Jedálny lístok.*$",
        "",
        text,
        flags=re.I
    )


    return " ".join(
        text.split()
    ).strip()



def parse_today(block):

    soup = None

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

        match = re.search(
            rf"Menu {i}:(.*?)(?=Menu {i+1}:|\Z)",
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

        raise Exception(
            "Dnešný deň sa nenašiel"
        )


    soup, meals = parse_today(
        block
    )


    return {

        "restaurant": "Kotolňa",

        "soup": soup,

        "meals": meals

    }



def main():

    data = scrape_kotolna()

    print(data)



if __name__ == "__main__":

    main()