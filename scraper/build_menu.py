import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from hoffer import scrape_hoffer
from quovadis import scrape_quovadis
from bellissimo import scrape_bellissimo
from buganka import scrape_buganka
from kotolna import scrape_kotolna
from hospudka import scrape_hospudka
from smichov import scrape_smichov
from sakura import scrape_sakura
from ukrba import scrape_ukrba


# koreň projektu
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "docs",
    "menu.json"
)


FLAG_PATH = os.path.join(
    BASE_DIR,
    ".menu_updated"
)



def should_update():

    now = datetime.now(
        ZoneInfo("Europe/Bratislava")
    )

    print(
        f"🕒 Slovenský čas: {now.strftime('%d.%m.%Y %H:%M:%S')}"
    )


    # iba pondelok - piatok
    if now.weekday() >= 5:

        print(
            "📅 Víkend - preskakujem aktualizáciu."
        )

        return False


    return True



# =====================================================
# SAKURA KATEGÓRIE
# =====================================================

def detect_sakura_category(item):

    number = item.get(
        "number"
    )


    if number is None:

        return "Polievky"



    if number in [
        "1",
        "2",
        "3",
        "4"
    ]:

        return "Sushi menu"



    if number in [
        "5",
        "6",
        "7",
        "8"
    ]:

        return "Teplé jedlá"



    if number in [
        "A",
        "B",
        "C",
        "D"
    ]:

        return "Týždenná ponuka"



    return "Ostatné"




def sort_sakura_menu(menu):


    category_order = {

        "Polievky": 1,

        "Sushi menu": 2,

        "Teplé jedlá": 3,

        "Týždenná ponuka": 4,

        "Ostatné": 5

    }



    number_order = {

        None: 0,

        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,

        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,

        "A": 9,
        "B": 10,
        "C": 11,
        "D": 12

    }



    return sorted(

        menu,

        key=lambda x: (

            category_order.get(
                x.get("category"),
                99
            ),

            number_order.get(
                x.get("number"),
                99
            )

        )

    )




def safe_scrape(
    restaurant_name,
    scraper
):

    try:

        result = scraper()

        return result


    except Exception as e:

        print(
            f"❌ {restaurant_name} chyba:",
            e
        )


        return {
            "restaurant": restaurant_name,
            "type": "error",
            "status": "error",
            "message": "Menu sa nepodarilo načítať",
            "image_url": "",
            "soup": {
                "price": "",
                "items": []
            },
            "meals": {
                "price": "",
                "items": []
            },
            "dessert": {
                "price": "",
                "items": []
            }
        }




def run_restaurant(
    data,
    name,
    scraper
):

    print(
        f"Načítavam {name}..."
    )


    result = safe_scrape(
        name,
        scraper
    )



    # =============================================
    # Sakura špeciálna úprava
    # =============================================

    if name == "Sakura":


        menu = result.get(
            "daily_menu",
            []
        )


        for item in menu:


            item["category"] = detect_sakura_category(
                item
            )



        result["daily_menu"] = sort_sakura_menu(
            menu
        )



    data.append(
        result
    )



    if result.get("status") == "error":

        print(
            f"⚠️ {name} chyba"
        )

    else:

        print(
            f"✅ {name} OK"
        )




def build():


    if not should_update():


        if os.path.exists(FLAG_PATH):

            os.remove(
                FLAG_PATH
            )


        return




    print(
        "🔄 Generujem obedové menu..."
    )


    data = []



    restaurants = [

        (
            "Hoffer",
            scrape_hoffer
        ),

        (
            "Quo Vadis",
            scrape_quovadis
        ),

        (
            "Bellissimo",
            scrape_bellissimo
        ),

        (
            "Buganka",
            scrape_buganka
        ),

        (
            "Hospúdka u Slováka",
            scrape_hospudka
        ),

        (
            "Kotolňa",
            scrape_kotolna
        ),

        (
            "Sakura",
            scrape_sakura
        ),

        (
            "Smíchov",
            scrape_smichov
        ),

        (
            "U Krba",
            scrape_ukrba
        )

    ]



    for name, scraper in restaurants:

        run_restaurant(
            data,
            name,
            scraper
        )



    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )



    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:


        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )



    with open(
        FLAG_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "updated"
        )



    print(
        f"✅ HOTOVO -> {OUTPUT_PATH}"
    )




if __name__ == "__main__":

    build()