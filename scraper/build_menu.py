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
            "status": "error",
            "message": "Menu sa nepodarilo načítať",
            "soup": "",
            "meals": []
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