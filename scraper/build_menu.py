import json
import os

from hoffer import scrape_hoffer
from quovadis import scrape_quovadis
from kotolna import scrape_kotolna


OUTPUT_PATH = "docs/menu.json"


def build():

    print("🔄 Generujem obedové menu...")

    data = []


    # HOFFER
    try:

        print("Načítavam Hoffera...")

        data.append(
            scrape_hoffer()
        )

        print("✅ Hoffer OK")


    except Exception as e:

        print(
            "❌ Hoffer error:",
            e
        )


    # QUO VADIS
    try:

        print("Načítavam Quo Vadis...")

        data.append(
            scrape_quovadis()
        )

        print("✅ Quo Vadis OK")


    except Exception as e:

        print(
            "❌ Quo Vadis error:",
            e
        )


    # KOTOLŇA
    try:

        print("Načítavam Kotolňu...")

        data.append(
            scrape_kotolna()
        )

        print("✅ Kotolňa OK")


    except Exception as e:

        print(
            "❌ Kotolňa error:",
            e
        )


    os.makedirs(
        "docs",
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


    print(
        "✅ HOTOVO -> docs/menu.json"
    )


if __name__ == "__main__":

    build()