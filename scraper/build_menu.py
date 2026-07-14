import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from hoffer import scrape_hoffer
from quovadis import scrape_quovadis
from bellissimo import scrape_bellissimo
from kotolna import scrape_kotolna
from hospudka import scrape_hospudka
from smichov import scrape_smichov


# koreň projektu (o úroveň vyššie ako scraper)
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


    # iba medzi 08:00 - 22:59
    if not (8 <= now.hour <= 22):

        print(
            "⏰ Mimo času aktualizácie (08:00 - 22:59)."
        )

        return False


    return True



def safe_scrape(
    restaurant_name,
    scraper
):

    try:

        return scraper()


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



    # HOFFER
    try:

        print(
            "Načítavam Hoffera..."
        )


        data.append(
            safe_scrape(
                "Hoffer",
                scrape_hoffer
            )
        )


        print(
            "✅ Hoffer OK"
        )


    except Exception as e:

        print(
            "❌ Hoffer error:",
            e
        )



    # QUO VADIS
    try:

        print(
            "Načítavam Quo Vadis..."
        )


        data.append(
            safe_scrape(
                "Quo Vadis",
                scrape_quovadis
            )
        )


        print(
            "✅ Quo Vadis OK"
        )


    except Exception as e:

        print(
            "❌ Quo Vadis error:",
            e
        )



    # BELLISSIMO
    try:

        print(
            "Načítavam Bellissimo..."
        )


        data.append(
            safe_scrape(
                "Bellissimo",
                scrape_bellissimo
            )
        )


        print(
            "✅ Bellissimo OK"
        )


    except Exception as e:

        print(
            "❌ Bellissimo error:",
            e
        )



    # HOSPÚDKA
    try:

        print(
            "Načítavam Hospúdku..."
        )


        data.append(
            safe_scrape(
                "Hospúdka u Slováka",
                scrape_hospudka
            )
        )


        print(
            "✅ Hospúdka OK"
        )


    except Exception as e:

        print(
            "❌ Hospúdka error:",
            e
        )



    # KOTOLŇA
    try:

        print(
            "Načítavam Kotolňu..."
        )


        data.append(
            safe_scrape(
                "Kotolňa",
                scrape_kotolna
            )
        )


        print(
            "✅ Kotolňa OK"
        )


    except Exception as e:

        print(
            "❌ Kotolňa error:",
            e
        )



    # SMÍCHOV
    try:

        print(
            "Načítavam Smíchov..."
        )


        data.append(
            safe_scrape(
                "Smíchov",
                scrape_smichov
            )
        )


        print(
            "✅ Smíchov OK"
        )


    except Exception as e:

        print(
            "❌ Smíchov error:",
            e
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



    # označíme, že prebehla aktualizácia
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