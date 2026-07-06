import requests
from bs4 import BeautifulSoup
from io import BytesIO
import pdfplumber
import re


PAGE_URL = "https://starakotolna.sk/#obedove-menu"


# -----------------------------
# 1. PDF LINKY
# -----------------------------
def get_pdf_links():
    r = requests.get(PAGE_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    pdfs = []

    for l in links:
        href = l["href"]
        if ".pdf" in href:
            if href.startswith("/"):
                href = "https://starakotolna.sk" + href
            pdfs.append(href)

    return pdfs


# -----------------------------
# 2. NAJLEPŠIE PDF
# -----------------------------
def get_pdf_url():
    pdfs = get_pdf_links()

    best = None
    best_score = -999

    for url in pdfs:
        try:
            r = requests.get(url)

            if "pdf" not in r.headers.get("Content-Type", ""):
                continue

            with pdfplumber.open(BytesIO(r.content)) as pdf:
                text = ""
                for p in pdf.pages:
                    t = p.extract_text()
                    if t:
                        text += t.lower()

                score = 0
                if "menu" in text: score += 2
                if "polievka" in text: score += 3
                if "menu 1" in text: score += 3
                if "menu 2" in text: score += 3
                if "menu 3" in text: score += 3

                if score > best_score:
                    best_score = score
                    best = url

        except:
            continue

    return best


# -----------------------------
# 3. SCRAPER (BLOCK PARSER)
# -----------------------------
def scrape_kotolna():

    pdf_url = get_pdf_url()

    if not pdf_url:
        return {"restaurant": "Kotolňa", "error": "no pdf"}

    r = requests.get(pdf_url)

    meals = []
    soup = ""

    try:
        with pdfplumber.open(BytesIO(r.content)) as pdf:

            full_text = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full_text += t.split("\n")

            current_menu = None
            buffer = []

            def flush():
                nonlocal current_menu, buffer, meals

                if current_menu and buffer:
                    meals.append({
                        "menu": current_menu,
                        "text": " ".join(buffer)
                    })

                buffer = []

            for line in full_text:

                line_lower = line.lower()

                # polievka
                if "polievka" in line_lower:
                    soup = line

                # menu start
                match = re.search(r"menu\s*[1-6]", line_lower)

                if match:
                    flush()
                    current_menu = match.group(0).upper()
                    continue

                # stop garbage
                if any(x in line_lower for x in ["krabica", "balné", "alobal"]):
                    continue

                # append do bloku
                if current_menu:
                    buffer.append(line.strip())

            flush()

    except Exception as e:
        return {"restaurant": "Kotolňa", "error": str(e)}

    return {
        "restaurant": "Kotolňa",
        "soup": soup,
        "meals": meals
    }