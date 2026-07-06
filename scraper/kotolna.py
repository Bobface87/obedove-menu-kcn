import requests
from bs4 import BeautifulSoup
from io import BytesIO
import pdfplumber
import re
import datetime


PAGE_URL = "https://starakotolna.sk/#obedove-menu"


SKIP_KEYWORDS = [
    "balné",
    "donáška",
    "príplatok",
    "objednávky",
    "otváracie",
    "www",
    "facebook",
    "instagram",
    "cena zahŕňa",
    "krabica",
    "alobal"
]


# -----------------------------
# 1. NAJDI VŠETKY PDF
# -----------------------------
def get_pdf_links():
    r = requests.get(PAGE_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    pdf_links = []

    for link in links:
        href = link["href"]

        if ".pdf" in href:
            if href.startswith("/"):
                href = "https://starakotolna.sk" + href
            pdf_links.append(href)

    return pdf_links


# -----------------------------
# 2. VÝBER NAJLEPŠIEHO PDF
# -----------------------------
def get_pdf_url():
    pdf_links = get_pdf_links()

    best_pdf = None
    best_score = -999

    for pdf_url in pdf_links:
        try:
            r = requests.get(pdf_url)

            if "pdf" not in r.headers.get("Content-Type", "").lower():
                continue

            with pdfplumber.open(BytesIO(r.content)) as pdf:
                text = ""
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t.lower()

                score = 0

                # pozitívne signály
                if "menu" in text: score += 2
                if "polievka" in text: score += 3
                if re.search(r"\d+,\d+", text): score += 1

                # negatívne signály
                if "krabica" in text: score -= 5
                if "balné" in text: score -= 5
                if "alobal" in text: score -= 5
                if "donáška" in text: score -= 5
                if "príplatok" in text: score -= 5

                if score > best_score:
                    best_score = score
                    best_pdf = pdf_url

        except:
            continue

    return best_pdf


# -----------------------------
# 3. FILTER RIADKOV
# -----------------------------
def is_valid_line(line: str) -> bool:
    line_lower = line.lower()

    if any(word in line_lower for word in SKIP_KEYWORDS):
        return False

    if not re.search(r"\d+,\d+", line):
        return False

    if len(line) < 10:
        return False

    return True


# -----------------------------
# 4. SCRAPER
# -----------------------------
def scrape_kotolna():

    pdf_url = get_pdf_url()

    if not pdf_url:
        return {
            "restaurant": "Kotolňa",
            "error": "No valid PDF found"
        }

    r = requests.get(pdf_url)

    if "pdf" not in r.headers.get("Content-Type", "").lower():
        return {
            "restaurant": "Kotolňa",
            "error": "Selected file is not PDF"
        }

    text = ""

    try:
        with pdfplumber.open(BytesIO(r.content)) as pdf:
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

    # -----------------------------
    # 5. DŇOVÝ PARSER (FIX PIATOK vs PONDELOK)
    # -----------------------------
    DAYS = {
        "pondelok": 0,
        "utorok": 1,
        "streda": 2,
        "štvrtok": 3,
        "piatok": 4,
        "sobota": 5,
        "nedeľa": 6
    }

    today_index = datetime.datetime.today().weekday()

    current_day = None

    meals = []
    soup = ""

    for line in lines:

        line_lower = line.lower()

        # detekcia dňa
        for day_name in DAYS:
            if day_name in line_lower:
                current_day = DAYS[day_name]

        # ignoruj iné dni
        if current_day is not None and current_day != today_index:
            continue

        # polievka
        if "polievka" in line_lower:
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