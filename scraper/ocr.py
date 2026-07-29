import requests
from io import BytesIO

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract


# ==================================================
# OCR nastavenie
# ==================================================

PSM_MODE = 4


# ==================================================
# Stiahnutie obrázka
# ==================================================

def download_image(image_url):

    response = requests.get(
        image_url,
        timeout=30
    )

    response.raise_for_status()

    return Image.open(
        BytesIO(response.content)
    )


# ==================================================
# Úprava obrázka
# ==================================================

def preprocess_image(image):

    # zväčšenie 4x
    image = image.resize(
        (
            image.width * 4,
            image.height * 4
        ),
        Image.Resampling.LANCZOS
    )

    # odtiene sivej
    image = image.convert("L")

    # kontrast
    image = ImageEnhance.Contrast(image).enhance(2.0)

    # jemné doostrenie
    image = image.filter(ImageFilter.SHARPEN)

    # uložiť pre kontrolu
    # image.save("debug_bellissimo.png")

    return image


# ==================================================
# OCR
# ==================================================

def extract_text_from_image(image_url):

    image = download_image(image_url)

    image = preprocess_image(image)

    text = pytesseract.image_to_string(
        image,
        lang="slk",
        config=f"--psm {PSM_MODE}"
    )

    return text


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    url = (
        "https://bellissimonitra.com/"
        "wp-content/uploads/2026/07/"
        "menu-bellissimo-32-722x1024.jpg"
    )

    text = extract_text_from_image(url)

    print()
    print("=" * 40)
    print("CELÝ OCR TEXT")
    print("=" * 40)
    print()

    print(text)

    print()
    print("=" * 40)
    print("KONIEC OCR TEXTU")
    print("=" * 40)