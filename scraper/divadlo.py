import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import urllib3
import re
import pdfplumber
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# NASTAVENIA
# ============================================================

BASE_URL = "http://www.cateringnitra.sk/"

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "divadlo_menu.pdf"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# ============================================================
# ČASOVÁ ZÓNA
# ============================================================

TIMEZONE = ZoneInfo(
    "Europe/Bratislava"
)


# ============================================================
# CENA MENU
# ============================================================

MENU_PRICE = "8,90 €"


# ============================================================
# ALERGÉNY
# ============================================================

ALLERGEN_NUMBERS = {
    "1", "2", "3", "4", "5",
    "6", "7", "8", "9", "10",
    "11", "12", "13", "14"
}


# ============================================================
# NAČÍTANIE WEBU
# ============================================================

def get_page():

    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        timeout=30,
        verify=False
    )

    response.raise_for_status()

    return response


# ============================================================
# HĽADANIE PDF CEZ TLAČIDLÁ
# ============================================================

def find_menu_pdf(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    buttons = soup.find_all(
        "button"
    )

    candidates = []

    for button in buttons:

        text = button.get_text(
            " ",
            strip=True
        )

        onclick = button.get(
            "onclick",
            ""
        ).strip()

        matches = re.findall(
            r"""['"]([^'"]+\.pdf(?:\?[^'"]*)?)['"]""",
            onclick,
            re.IGNORECASE
        )

        for pdf_path in matches:

            pdf_url = urljoin(
                BASE_URL,
                pdf_path
            )

            candidates.append(
                pdf_url
            )

    # --------------------------------------------------------
    # ODSTRÁNENIE DUPLÍCIT
    # --------------------------------------------------------

    unique_candidates = []

    seen_urls = set()

    for url in candidates:

        if url in seen_urls:
            continue

        seen_urls.add(url)

        unique_candidates.append(url)

    if not unique_candidates:

        return None

    return unique_candidates[0]


# ============================================================
# STIAHNUTIE A KONTROLA PDF
# ============================================================

def download_pdf(pdf_url):

    response = requests.get(
        pdf_url,
        headers=HEADERS,
        timeout=30,
        verify=False
    )

    response.raise_for_status()

    # --------------------------------------------------------
    # Kontrola, či ide skutočne o PDF
    # --------------------------------------------------------

    if not response.content.startswith(
        b"%PDF"
    ):

        raise Exception(
            "Stiahnutý súbor nie je platné PDF."
        )

    # --------------------------------------------------------
    # Uloženie PDF
    # --------------------------------------------------------

    OUTPUT_FILE.write_bytes(
        response.content
    )

    return OUTPUT_FILE


# ============================================================
# ODDELENIE ALERGÉNOV
# ============================================================

def split_allergens(text):

    text = text.strip()

    # --------------------------------------------------------
    # Hľadáme súvislý blok alergénov
    # na konci riadku.
    # --------------------------------------------------------

    match = re.search(
        r"(?:\s+)(\d+(?:\s+\d+)*)$",
        text
    )

    if not match:

        return text, []

    allergen_text = match.group(1)

    numbers = allergen_text.split()

    # --------------------------------------------------------
    # Kontrola, či ide o čísla alergénov.
    # --------------------------------------------------------

    if not all(
        number in ALLERGEN_NUMBERS
        for number in numbers
    ):

        return text, []

    clean_text = (
        text[:match.start()]
        .strip()
    )

    return clean_text, numbers


# ============================================================
# SPRACOVANIE JEDNÉHO MENU
# ============================================================

def parse_menu_line(line):

    line = line.strip()

    match = re.match(
        r"^Menu\s+(\d+):\s*(.*)$",
        line,
        re.IGNORECASE
    )

    if not match:

        return None

    menu_number = int(
        match.group(1)
    )

    content = match.group(2).strip()

    # --------------------------------------------------------
    # HMOTNOSŤ
    # --------------------------------------------------------

    weight_match = re.match(
        r"^(\d+\s*g)\s+(.*)$",
        content,
        re.IGNORECASE
    )

    if weight_match:

        weight = weight_match.group(1)

        content = (
            weight_match.group(2)
            .strip()
        )

    else:

        weight = None

    # --------------------------------------------------------
    # ALERGÉNY
    # --------------------------------------------------------

    name, allergens = split_allergens(
        content
    )

    # --------------------------------------------------------
    # JEDNOTNÁ ŠTRUKTÚRA MENU
    # --------------------------------------------------------

    return {
        "number": menu_number,
        "price": MENU_PRICE,
        "name": name,
        "weight": weight,
        "description": None,
        "allergens": allergens
    }


# ============================================================
# SPRACOVANIE POLIEVKY
# ============================================================

def parse_soup_line(line):

    match = re.match(
        r"^Polievka:\s*(.*)$",
        line,
        re.IGNORECASE
    )

    if not match:

        return None

    content = match.group(1).strip()

    name, allergens = split_allergens(
        content
    )

    return {
        "name": name,
        "weight": None,
        "description": None,
        "allergens": allergens
    }


# ============================================================
# SPRACOVANIE DŇA
# ============================================================

def parse_day_block(
    lines,
    start_index
):

    line = lines[start_index].strip()

    # --------------------------------------------------------
    # DEŇ + DÁTUM + STATUS
    # --------------------------------------------------------

    match = re.match(
        r"^([A-ZÁČĎÉÍĽŇÓÔŔŠŤÚÝŽ]+):\s*"
        r"(\d{2}\.\d{2}\.\d{4})"
        r"(?:\s*\((.*?)\))?$",
        line
    )

    if not match:

        return None, start_index + 1

    day = match.group(1)

    date = match.group(2)

    status = match.group(3)

    # --------------------------------------------------------
    # DEŇ SO STATUSOM
    # --------------------------------------------------------

    if status:

        return {
            "day": day,
            "date": date,
            "status": status,
            "soup": None,
            "menus": []
        }, start_index + 1

    # --------------------------------------------------------
    # OTVORENÝ DEŇ
    # --------------------------------------------------------

    day_data = {
        "day": day,
        "date": date,
        "soup": None,
        "menus": []
    }

    index = start_index + 1

    # --------------------------------------------------------
    # ČÍTAME RIADKY DŇA
    # --------------------------------------------------------

    while index < len(lines):

        current = lines[index].strip()

        # ----------------------------------------------------
        # Prázdny riadok
        # ----------------------------------------------------

        if not current:

            index += 1
            continue

        # ----------------------------------------------------
        # Nový deň
        # ----------------------------------------------------

        if re.match(
            r"^[A-ZÁČĎÉÍĽŇÓÔŔŠŤÚÝŽ]+:"
            r"\s*\d{2}\.\d{2}\.\d{4}",
            current
        ):

            break

        # ----------------------------------------------------
        # POLIEVKA
        # ----------------------------------------------------

        soup = parse_soup_line(
            current
        )

        if soup:

            day_data["soup"] = soup

            index += 1

            continue

        # ----------------------------------------------------
        # MENU
        # ----------------------------------------------------

        menu = parse_menu_line(
            current
        )

        if menu:

            day_data["menus"].append(
                menu
            )

            index += 1

            continue

        # ----------------------------------------------------
        # Ostatný text ignorujeme.
        # ----------------------------------------------------

        index += 1

    return day_data, index


# ============================================================
# EXTRAKCIA RIADKOV Z PDF
# ============================================================

def extract_pdf_lines():

    if not OUTPUT_FILE.exists():

        raise FileNotFoundError(
            f"PDF neexistuje: "
            f"{OUTPUT_FILE}"
        )

    lines = []

    with pdfplumber.open(
        OUTPUT_FILE
    ) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:

                continue

            page_lines = text.splitlines()

            for line in page_lines:

                line = line.strip()

                if line:

                    lines.append(line)

    return lines


# ============================================================
# IDENTIFIKÁCIA TÝŽDŇA
# ============================================================

def find_week(lines):

    for line in lines:

        match = re.search(
            r"(\d{2}\.\d{2}\.\d{4})"
            r"\s*-\s*"
            r"(\d{2}\.\d{2}\.\d{4})",
            line
        )

        if match:

            return (
                f"{match.group(1)} - "
                f"{match.group(2)}"
            )

    return None


# ============================================================
# AKTUÁLNY DÁTUM
# ============================================================

def get_current_date():

    now = datetime.now(
        TIMEZONE
    )

    return now.strftime(
        "%d.%m.%Y"
    )


# ============================================================
# FILTROVANIE AKTUÁLNEHO DŇA
# ============================================================

def filter_current_day(days):

    current_date = get_current_date()

    for day in days:

        if day.get("date") == current_date:

            return [
                day
            ]

    return []


# ============================================================
# HLAVNÝ PARSER PDF
# ============================================================

def parse_divadlo_pdf():

    lines = extract_pdf_lines()

    week = find_week(
        lines
    )

    days = []

    index = 0

    while index < len(lines):

        line = lines[index].strip()

        # ----------------------------------------------------
        # Hľadáme začiatok dňa.
        # ----------------------------------------------------

        if re.match(
            r"^[A-ZÁČĎÉÍĽŇÓÔŔŠŤÚÝŽ]+:"
            r"\s*\d{2}\.\d{2}\.\d{4}",
            line
        ):

            day_data, next_index = (
                parse_day_block(
                    lines,
                    index
                )
            )

            if day_data:

                days.append(
                    day_data
                )

            index = next_index

            continue

        index += 1

    # --------------------------------------------------------
    # PONECHÁME IBA AKTUÁLNY DEŇ
    # --------------------------------------------------------

    current_day = filter_current_day(
        days
    )

    return {
        "week": week,
        "days": current_day
    }


# ============================================================
# KOMPLETNÉ SPRACOVANIE DIVADLA
# ============================================================

def scrape_divadlo():

    print(
        "Načítavam Divadlo..."
    )

    # --------------------------------------------------------
    # 1. Načítanie webu
    # --------------------------------------------------------

    response = get_page()

    # --------------------------------------------------------
    # 2. Nájdeme PDF
    # --------------------------------------------------------

    pdf_url = find_menu_pdf(
        response.text
    )

    if not pdf_url:

        raise Exception(
            "PDF pre Obedové menu "
            "nebolo nájdené."
        )

    # --------------------------------------------------------
    # 3. Stiahneme PDF
    # --------------------------------------------------------

    pdf_file = download_pdf(
        pdf_url
    )

    # --------------------------------------------------------
    # 4. Spracujeme PDF
    # --------------------------------------------------------

    data = parse_divadlo_pdf()

    # --------------------------------------------------------
    # 5. Výsledok
    # --------------------------------------------------------

    return {
        "restaurant": "Divadlo",
        "pdf_url": pdf_url,
        "pdf_file": str(pdf_file),
        "week": data["week"],
        "days": data["days"]
    }


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        data = scrape_divadlo()

        print(
            "Divadlo OK"
        )

        return data

    except Exception as e:

        print(
            f"Divadlo chyba: {e}"
        )

        return None


if __name__ == "__main__":

    main()