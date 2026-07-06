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


# -----------------------------
# 1. NAJDI SPRÁVNY PDF
# -----------------------------
def get_pdf_url():
    r = requests.get(PAGE_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    for link in links:
        href = link["href"]

        # 🔥 PRESNÝ FILTER – iba Kotolňa menu PDF
        if "obedove-menu-kotolna" in href.lower():
            return href

    return None


# -----------------------------
# 2. FILTER RIADKOV
# -----------------------------
def is_valid_line(line: str) -> bool:
    line_lower = line.lower()

    # ignoruj bordel texty
    if any(word in line_lower for word in SKIP_KEYWORDS):
        return False

    # musí obsahovať cenu
    if not re.search(r"\d+,\d+", line):
        return False

    # minimálna dĺžka
    if len(line) < 10:
        return False

    return True


# -----------------------------
# 3. SCRAPER
# -----------------------------
def scrape_kotolna():

    pdf_url = get_pdf_url()

    if not pdf_url:
        return {
            "restaurant": "Kotolňa",
            "error": "PDF link not found"
        }

    # fix relatívnych linkov
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

        # polievka
        if "POLIEVKA" in line.upper():
            soup = line

        # cena
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