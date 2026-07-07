import requests
from bs4 import BeautifulSoup
import re


URL = "https://www.penzion-hoffer.sk/22411/obedove-menu"


def extract_price(text):

    match = re.search(
        r"(\d+,\d+)\s*€",
        text
    )

    if match:
        return float(
            match.group(1).replace(",", ".")
        )

    return None


def clean_text(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = text.replace(
        "POLIEVKA",
        ""
    )

    return text.strip()



def scrape_hoffer():

    print("Načítavam Hoffera...")


    headers = {
        "User-Agent": "Mozilla/5.0"
    }


    res = requests.get(
        URL,
        headers=headers,
        timeout=20
    )

    res.raise_for_status()


    soup = BeautifulSoup(
        res.text,
        "html.parser"
    )


    # nájdeme iba hlavnú časť stránky
    content = soup.find(
        "main"
    )


    if not content:

        content = soup


    text = content.get_text(
        "\n",
        strip=True
    )


    lines = [
        x.strip()
        for x in text.split("\n")
        if x.strip()
    ]


    soup_text = ""

    meals = []


    current = ""


    for line in lines:


        if "POLIEVKA" in line.upper():

            soup_text = line
            continue



        # hľadáme riadky s cenou

        if re.search(
            r"\d+,\d+\s*€",
            line
        ):

            price = extract_price(line)


            clean = re.sub(
                r"\d+,\d+\s*€",
                "",
                line
            )


            clean = clean_text(clean)


            if clean and price:

                meals.append(
                    {
                        "name": clean,
                        "price": price
                    }
                )


    return {
        "restaurant": "Hoffer",
        "soup": clean_text(soup_text),
        "meals": meals[:6]
    }