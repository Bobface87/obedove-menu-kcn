import re
import json
from datetime import datetime
from io import BytesIO

import requests
import pdfplumber
from bs4 import BeautifulSoup


MAIN_URL = "https://sakura1.eatbu.com/?lang=sk#"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 Windows NT 10.0 "
        "Chrome/137 Safari/537.36"
    )
}


DAY_CODES = {
    0: "PO",
    1: "UT",
    2: "ST",
    3: "ŠT",
    4: "PI",
}



def today_code():

    d = datetime.today().weekday()

    if d > 4:
        raise Exception(
            "Sakura cez víkend menu nemá"
        )

    return DAY_CODES[d]



def get_pdf_url():

    r = requests.get(
        MAIN_URL,
        headers=HEADERS,
        timeout=20
    )

    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    code = today_code()

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        if (
            ".pdf" in href.lower()
            and f"MENU-{code}" in href.upper()
        ):
            return href


    raise Exception(
        "PDF nenájdené"
    )



def download_pdf():

    url = get_pdf_url()

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    r.raise_for_status()

    return BytesIO(
        r.content
    )



def extract_columns():

    pdf = download_pdf()


    with pdfplumber.open(pdf) as doc:

        page = doc.pages[0]

        words = page.extract_words()


        left=[]
        right=[]


        for w in words:

            if w["x0"] < 300:
                left.append(w)

            else:
                right.append(w)



        def build(items):

            items = sorted(
                items,
                key=lambda x:(
                    x["top"],
                    x["x0"]
                )
            )


            lines=[]

            current=[]

            last=None


            for w in items:

                if (
                    last is None
                    or abs(w["top"]-last)<5
                ):

                    current.append(
                        w["text"]
                    )

                else:

                    lines.append(
                        " ".join(current)
                    )

                    current=[
                        w["text"]
                    ]


                last=w["top"]


            if current:
                lines.append(
                    " ".join(current)
                )


            return lines


        return (
            build(left),
            build(right)
        )



def clean(t):

    t=re.sub(
        r"/.*?/",
        "",
        t
    )

    t=re.sub(
        r"\s+",
        " ",
        t
    )

    return t.strip()



def get_price(t):

    m=re.search(
        r"\d+,\d+\s*€",
        t
    )

    return (
        m.group(0)
        if m
        else None
    )



def get_weight(t):

    m=re.search(
        r"\d+\s*(g|ks)",
        t
    )

    return (
        m.group(0)
        if m
        else None
    )



# -----------------------------
# POLIEVKY
# -----------------------------


def parse_soups(lines):

    text=" ".join(lines)

    result=[]


    patterns=[
        "Rybacia polievka",
        "Ostrokyslá polievka"
    ]


    for p in patterns:

        m=re.search(
            p+r".*?(\d+,\d+\s*€)",
            text
        )

        if m:

            result.append(
                {
                    "name":p,
                    "price":m.group(1)
                }
            )


    return result



# -----------------------------
# SUSHI 1-4
# -----------------------------


def parse_sushi(lines):

    text=" ".join(lines)

    result=[]


    blocks=re.split(
        r"(?=\d+\.\s)",
        text
    )


    for b in blocks:

        m=re.search(
            r"(\d+)\.\s*(.*?)\s*(\d+,\d+\s*€)",
            b
        )


        if m and int(m.group(1)) <= 4:

            result.append(
                {
                    "number":m.group(1),
                    "name":clean(m.group(2)),
                    "price":m.group(3),
                    "description":clean(b)
                }
            )


    return result



# -----------------------------
# UDON 5
# -----------------------------


def parse_udon(text):

    item={

        "number":"5",
        "name":"UDON REZANCE",
        "weight":"200g",
        "variants":[],
        "description":""

    }


    variants=[]


    for m in re.finditer(
        r"(\d+,\d+\s*€)\s*([abc])\)\s*(.*?)\s*(?=\d+g|\)|$)",
        text
    ):

        variants.append(
            {
                "label":m.group(2)+")",
                "name":clean(m.group(3)),
                "price":m.group(1)
            }
        )


    # posledné c)
    m=re.search(
        r"c\)\s*(.*?)\s*(\d+,\d+\s*€)",
        text
    )


    if m:

        variants.append(
            {
                "label":"c)",
                "name":clean(m.group(1)),
                "price":m.group(2)
            }
        )


    item["variants"]=variants


    desc=re.split(
        r"Restované",
        text
    )


    if len(desc)>1:

        item["description"] = (
            "Restované"
            + desc[1]
        )


    return item



# -----------------------------
# DAILY 6-8
# -----------------------------


def parse_hot(lines):

    text=" ".join(lines)

    result=[]


    for num in ["6","7","8"]:

        m=re.search(
            rf"{num}\.\s*(.*?)(?=\s[678]\.|$)",
            text
        )


        if m:

            block=m.group(1)

            result.append(
                {
                    "number":num,
                    "name":clean(block.split("200g")[0]),
                    "weight":get_weight(block),
                    "price":get_price(block),
                    "description":clean(block)
                }
            )


    return result



# -----------------------------
# WEEKLY A-D
# -----------------------------


def parse_weekly(lines):

    text=" ".join(lines)

    result=[]


    for letter in ["A","B","C","D"]:

        m=re.search(
            rf"{letter}\.\s*(.*?)(?=\s[A-D]\.|$)",
            text
        )

        if m:

            block=m.group(1)

            result.append(
                {
                    "number":letter,
                    "name":clean(
                        block.split("250g")[0]
                    ),
                    "weight":get_weight(block),
                    "price":get_price(block),
                    "description":clean(block)
                }
            )


    return result



def scrape_sakura():

    print(
        "Načítavam Sakuru..."
    )


    left,right=extract_columns()


    left_text=" ".join(left)
    right_text=" ".join(right)


    udon=parse_udon(
        right_text
    )


    daily=[
        udon
    ]


    daily.extend(
        parse_hot(right)
    )


    return {

        "restaurant":"Sakura",

        "soups":parse_soups(right),

        "sushi":parse_sushi(left),

        "daily_menu":daily,

        "weekly_menu":parse_weekly(left+right)

    }



if __name__=="__main__":

    data=scrape_sakura()


    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )