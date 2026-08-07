import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re


URL = "https://www.penzionartin.sk/obedove-menu-na-tento-tyzden"



def clean_url(url):

    if not url:
        return ""

    if "," in url:
        url = url.split(",")[0]

    url = re.sub(
        r"\s+\d+x$",
        "",
        url
    )

    url = url.strip()


    # Wix škálovanie odstránime až po výbere obrázka

    match = re.search(
        r"(.+\.(?:jpg|jpeg|png|webp))",
        url,
        re.IGNORECASE
    )


    if match:

        return match.group(1)


    return url




def get_week_dates():

    today = datetime.today()


    monday = today - timedelta(
        days=today.weekday()
    )


    friday = monday + timedelta(
        days=4
    )


    return {

        "monday_day": str(monday.day),

        "monday_month": str(monday.month),

        "friday_day": str(friday.day),

        "friday_month": str(friday.month)

    }




def get_week_patterns():

    dates = get_week_dates()


    return [

        f"{dates['monday_day']}_{dates['monday_month']}",

        f"{dates['friday_day']}_{dates['friday_month']}",


        f"{dates['monday_day']}-{dates['monday_month']}",

        f"{dates['friday_day']}-{dates['friday_month']}",


        f"{dates['monday_day']}.{dates['monday_month']}",

        f"{dates['friday_day']}.{dates['friday_month']}",


        f"{dates['monday_day']}%20",

        f"{dates['friday_day']}%20"

    ]




def score_image(url):

    score = 0


    u = url.lower()



    # -----------------------------
    # vyradenie nepotrebných obrázkov
    # -----------------------------

    banned = [

        "logo",

        "icon",

        "facebook",

        "instagram",

        "favicon",


        "w_25",

        "w_50",

        "w_135",

        "w_186",

        "w_192",

        "w_270",

        "w_372"

    ]


    for item in banned:

        if item in u:

            return -100



    # -----------------------------
    # formát
    # -----------------------------

    if ".jpg" in u:

        score += 5


    if ".webp" in u:

        score += 5



    # -----------------------------
    # veľkosť Wix obrázka
    # -----------------------------

    if "w_749" in u:

        score += 10


    if "w_1055" in u:

        score += 10


    if "h_1022" in u:

        score += 10


    if "h_1440" in u:

        score += 10



    # -----------------------------
    # názov súboru
    # -----------------------------

    if "obed" in u:

        score += 20


    if "menu" in u:

        score += 20


    if "artin" in u:

        score += 10



    # -----------------------------
    # aktuálny týždeň
    # -----------------------------

    found = 0


    for pattern in get_week_patterns():

        if pattern in u:

            found += 1



    score += found * 20



    # bonus ak nájde oba dátumy
    if found >= 2:

        score += 30



    return score





def find_menu_image():

    print(
        "🔎 Hľadám obrázok Artin..."
    )


    r = requests.get(

        URL,

        timeout=20,

        headers={

            "User-Agent":

            "Mozilla/5.0"

        }

    )


    r.raise_for_status()



    soup = BeautifulSoup(

        r.text,

        "html.parser"

    )



    images = []



    for img in soup.find_all("img"):


        for attr in [

            "src",

            "data-src",

            "srcset"

        ]:


            value = img.get(attr)


            if not value:

                continue



            for part in value.split(","):


                raw_url = part.strip()



                if raw_url.startswith("http"):

                    images.append(raw_url)




    images = list(

        dict.fromkeys(images)

    )




    scored = []



    for raw in images:


        score = score_image(raw)


        if score > 0:


            scored.append(

                (

                    score,

                    raw

                )

            )




    scored.sort(

        reverse=True,

        key=lambda x: x[0]

    )




    print(

        "\n📊 Hodnotenie obrázkov:"

    )



    for score, img in scored:


        print(

            score,

            img

        )




    if not scored:

        return None




    best_score, best_raw = scored[0]



    print(

        "\n✅ Vybraný RAW obrázok:",

        best_raw

    )



    clean = clean_url(

        best_raw

    )



    print(

        "✅ Čistý obrázok:",

        clean

    )



    return clean






def scrape_artin():


    print(

        "Načítavam Artin..."

    )



    image = find_menu_image()



    if not image:


        raise Exception(

            "Obrázok menu Artin nenájdený"

        )




    return {


        "restaurant": "Artin",


        "type": "image_menu",


        "image_url": image,


        "soup": None,


        "meals": []


    }





def main():

    import json



    data = scrape_artin()



    print(

        json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        )

    )





if __name__ == "__main__":

    main()