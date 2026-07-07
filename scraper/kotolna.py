import re
from datetime import datetime
from io import BytesIO

import pdfplumber
import requests


PDF_URL = "https://starakotolna.sk/wp-content/uploads/2026/07/Obedove-menu-Kotolna-262026.pdf"


DAY_NAMES = [
    "Pondelok",
    "Utorok",
    "Streda",
    "Štvrtok",
    "Piatok",
]


def download_pdf():

    print("⬇ Sťahujem PDF...")

    r = requests.get(PDF_URL, timeout=20)
    r.raise_for_status()

    return BytesIO(r.content)


def load_text():

    pdf_file = download_pdf()

    text = ""

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            t = page.extract_text()

            if t:
                text += t + "\n"

    return text


def today_name():

    return DAY_NAMES[datetime.today().weekday()]


def split_days(text):

    pattern = r"Denné menu na (?:Pondelok|Utorok|Streda|Štvrtok|Piatok).*?(?=Denné menu na|\Z)"

    return [
        m.group(0)
        for m in re.finditer(pattern, text, flags=re.S)
    ]


def find_today_block(text):

    today = today_name()

    blocks = split_days(text)

    for block in blocks:

        if f"Denné menu na {today}" in block:
            return block

    return None


def main():

    print("Načítavam PDF...")

    text = load_text()

    block = find_today_block(text)

    if not block:

        print("❌ Dnešný deň sa nenašiel.")
        return

    print("=" * 80)
    print(block)
    print("=" * 80)


if __name__ == "__main__":
    main()