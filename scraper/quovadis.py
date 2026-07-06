import requests
from bs4 import BeautifulSoup

URL = "https://www.quovadisnitra.sk/tyzdenne-menu/"

def scrape_quovadis():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")

    return {
        "restaurant": "Quo Vadis",
        "soup": "",
        "meals": [
            {"name": "test menu (parsujeme neskôr)", "price": 0}
        ]
    }