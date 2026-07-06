import requests
from bs4 import BeautifulSoup
from io import BytesIO
import pdfplumber
import re


PAGE_URL = "https://starakotolna.sk/castellum-cafe/"


SKIP_KEYWORDS = [
    "balné",
    "donáška",
    "príplatok",
    "objednávky",
    "otváracie",
    "www",
    "menu podávame",
    "facebook",
    "instagram",
    "cena zahŕňa"
]


def get_pdf_url():
    r = requests.get(PAGE_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"].lower()

        if ".pdf" in href:
            return a["href"]

    return None


def is_valid_line(line: str) -> bool:
    line_lower = line.lower()

    # vyradenie bordelu
    if any(word in line_lower for word in SKIP_KEYWORDS):
        return False

    # musí obsahovať cenu
    if not re.search(r"\d+,\d+", line):
        return False

    # minimálna dĺžka (odfiltruje hlúposti)
    if len(line) < 10:
        return False

    return True


def scrape_kotolna():

    pdf_url = get_pdf_url()

    if not pdf_url:
        return {
            "restaurant": "Kotolňa",
            "error": "PDF link not found"
        }

    if pdf_url.startswith("/"):
        pdf_url = "https://starakotolna.sk" + pdf_url

    r = requests.get(pdf_url)

    if "pdf" not in r.headers.get("Content-Type", "").lower():
        return {
            "restaurant": "Kotolňa",
            "error": "URL does not return PDF"
        }

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

        # ❌ filter bordelu
        if not is_valid_line(line):
            continue

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