import requests
from bs4 import BeautifulSoup
from io import BytesIO
import pdfplumber
import re


PAGE_URL = "https://starakotolna.sk/castellum-cafe/"


def get_pdf_url():
    r = requests.get(PAGE_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    # nájdi všetky linky
    for a in soup.find_all("a", href=True):
        if "obedove" in a.text.lower() or "menu" in a.text.lower():
            return a["href"]

    return None


def scrape_kotolna():

    pdf_url = get_pdf_url()

    if not pdf_url:
        return {
            "restaurant": "Kotolňa",
            "error": "PDF link not found"
        }

    r = requests.get(pdf_url)

    pdf_file = BytesIO(r.content)

    text = ""

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return {
            "restaurant": "Kotolňa",
            "error": str(e)
        }

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    meals = []
    soup = ""

    for line in lines:

        if "POLIEVKA" in line.upper():
            soup = line

        price_match = re.search(r"\d+,\d+", line)
        price = float(price_match.group(0).replace(",", ".")) if price_match else None

        if price:
            name = re.sub(r"\d+,\d+.*", "", line).strip()
            meals.append({
                "name": name,
                "price": price
            })

    return {
        "restaurant": "Kotolňa",
        "soup": soup,
        "meals": meals[:6]
    }