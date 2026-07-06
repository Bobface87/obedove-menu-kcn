import pytesseract
from PIL import Image
import requests
from io import BytesIO
import re


def download_image(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))


def extract_text_from_image(url):
    img = download_image(url)
    text = pytesseract.image_to_string(img, lang="slk+eng")
    return text


def extract_meals(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    meals = []
    soup = ""

    for i, line in enumerate(lines):

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

    return soup, meals[:6]