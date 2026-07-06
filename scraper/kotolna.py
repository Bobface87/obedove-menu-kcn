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
# 1. NAJDI PDF LINKY
# -----------------------------
def get_pdf_links():
    r = requests.get(PAGE_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    pdf_links = []

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if ".pdf" in href:
            if href.startswith("/"):
                href = "https://starakotolna.sk" + href
            pdf_links.append(href)

    return pdf_links


# -----------------------------
# 2. VÝBER NAJLEPŠIEHO PDF (score)
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

                if "menu" in text: score += 2
                if "polievka" in text: score += 3
                if re.search(r"\d+,\d+", text): score += 1

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

    if len(line) < 8:
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

    # -----------------------------
    # 5. PDF → WORDS PARSING (FIX)
    # -----------------------------
    meals = []
    soup = ""

    try:
        with pdfplumber.open(BytesIO(r.content)) as pdf:

            for page in pdf.pages:

                words = page.extract_words()

                lines = []
                current_line = ""
                last_top = None

                for w in words:
                    top = round(w["top"])

                    if last_top is None:
                        last_top = top

                    if abs(top - last_top) > 3:
                        lines.append(current_line.strip())
                        current_line = w["text"]
                        last_top = top
                    else:
                        current_line += " " + w["text"]

                if current_line:
                    lines.append(current_line.strip())

                # -------------------------
                # PARSING JEDÁL
                # -------------------------
                for line in lines:

                    if not is_valid_line(line):
                        continue

                    if "polievka" in line.lower():
                        soup = line

                    price_match = re.search(r"\d+,\d+", line)
                    price = float(price_match.group(0).replace(",", ".")) if price_match else None

                    if price:
                        name = re.sub(r"\d+,\d+.*", "", line).strip()

                        meals.append({
                            "name": name,
                            "price": price
                        })

    except Exception as e:
        return {
            "restaurant": "Kotolňa",
            "error": str(e)
        }

    return {
        "restaurant": "Kotolňa",
        "soup": soup,
        "meals": meals
    }