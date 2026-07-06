import requests

URL = "https://www.quovadisnitra.sk/tyzdenne-menu/"


def scrape_quovadis():
    return {
        "restaurant": "Quo Vadis",
        "type": "link_menu",
        "menu_url": URL,
        "soup": "",
        "meals": []
    }