import requests
from io import BytesIO

from PIL import Image, ImageEnhance
import pytesseract



def download_image(image_url):
    """
    Stiahne obrázok menu z URL.
    """

    response = requests.get(
        image_url,
        timeout=30
    )

    response.raise_for_status()

    return Image.open(
        BytesIO(response.content)
    )



def preprocess_image(image):
    """
    Základné vylepšenie obrázka pre OCR.
    """

    image = image.resize(
        (
            image.width * 2,
            image.height * 2
        )
    )

    image = image.convert(
        "L"
    )

    image = ImageEnhance.Contrast(
        image
    ).enhance(
        1.5
    )

    return image



def extract_text_from_image(image_url):
    """
    OCR obrázka.
    """

    image = download_image(
        image_url
    )

    image = preprocess_image(
        image
    )

    text = pytesseract.image_to_string(
        image,
        lang="slk"
    )

    return text



if __name__ == "__main__":

    TEST_IMAGE = (
        "https://www.quovadisnitra.sk/"
        "wp-content/uploads/2026/07/"
        "pondelok-10-724x1024.jpg"
    )


    result = extract_text_from_image(
        TEST_IMAGE
    )


    print()
    print("=" * 40)
    print("CELÝ OCR TEXT")
    print("=" * 40)
    print()


    print(result)


    print()
    print("=" * 40)
    print("KONIEC OCR TEXTU")
    print("=" * 40)