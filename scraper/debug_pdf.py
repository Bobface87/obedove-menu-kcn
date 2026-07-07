import pdfplumber
from io import BytesIO
import requests

PDF_URL = "https://starakotolna.sk/wp-content/uploads/2026/07/Obedove-menu-Kotolna-262026.pdf"


r = requests.get(PDF_URL)

with pdfplumber.open(BytesIO(r.content)) as pdf:

    print("=" * 80)
    print("POČET STRÁN:", len(pdf.pages))
    print("=" * 80)

    for page_no, page in enumerate(pdf.pages, start=1):

        print(f"\n\n########## STRANA {page_no} ##########\n")

        text = page.extract_text()

        print("===== extract_text() =====")
        print(text)

        print("\n\n===== extract_words() =====")

        words = page.extract_words()

        for w in words[:300]:
            print(
                f"{w['text']:<25} "
                f"x={w['x0']:.1f} "
                f"top={w['top']:.1f}"
            )

        print("\n\n===== KONIEC STRANY =====")