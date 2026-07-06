import pdfplumber
import requests
from io import BytesIO
import re


def download_pdf(url):
    response = requests.get(url)
    return BytesIO(response.content)


def extract_text_from_pdf(url):
    pdf_file = download_pdf(url)

    text = ""

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


def parse_meals(text):
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
        "soup": soup,
        "meals": meals[:6]
    }