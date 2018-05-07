import os
import json
import math
import requests
from collections import OrderedDict

import pandas as pd

DATA_FILES = {
    "bm01": {
        "filename": "bm-2018-jena-01.json",
        "url": "http://statistiken.jena.de/instantatlas/wahlstatistik2018_ob_wg1/data.js"
    },
    "bm02": {
        "filename": "bm-2018-jena-02.json",
        "url": "http://statistiken.jena.de/instantatlas/wahlstatistik/data.js",
    },

    "stats-index": {
        "filename": "jena-stat-index.json",
        "url": "http://statistiken.jena.de/instantatlas/stadtbezirksstatistik/data.js"
    },

    "stats-shape": {
        "filename": "jena-stat-shape.json",
        "url": "http://statistiken.jena.de/instantatlas/stadtbezirksstatistik/_Jena_StatBez.shp1.js",
    },
    "bm-shape": {
        "filename": "bm-2018-jena-shape.json",
        "url": "http://statistiken.jena.de/instantatlas/wahlstatistik2018_ob_wg1/_WBZ_Jena_20170630_extra.shp1.js",
    },
}

BEZIRK_MAPPING = {
    'Ammerbach Ort': ['045 Kita Ammberbach'],
    'Beutenberg / Winzerlaer Straße': [''],
    'Burgau Ort': [''],
    'Closewitz': [''], 
    'Cospeda': [''], 
    'Drackendorf': [''], 
    'Drackendorf / Lobeda-Ost': [''],
    'Göschwitz': [''], 
    'Ilmnitz': [''], 
    'Isserstedt': [''], 
    'Jena-Nord': [''], 
    'Jenaprießnitz': [''],
    'Jena-Süd': [''], 
    'Jena-West': [''], 
    'Jena-Zentrum': [''], 
    'Krippendorf': [''], 
    'Kunitz': [''],
    'Laasan': [''], 
    'Leutra': [''], 
    'Lichtenhain Ort': [''], 
    'Lobeda-Altstadt': [''],
    'Lobeda-Ost': [''], 
    'Lobeda-West': [''], 
    'Löbstedt Ort': [''], 
    'Lützeroda': [''], 
    'Maua': [''],
    'Mühlenstraße': [''], 
    'Münchenroda': [''], 
    'Nord II': [''], 
    'Remderoda': [''],
    'Ringwiese Flur Burgau': [''], 
    'Vierzehnheiligen': [''],
    'Wenigenjena / Kernberge': [''], 
    'Wenigenjena / Schlegelsberg': [''],
    'Wenigenjena Ort': [''], 
    'Winzerla': [''], 
    'Wogau': [''], 
    'Wöllnitz': [''],
    'Ziegenhain Ort': [''], 
    'Ziegenhainer Tal': [''], 
    'Zwätzen': [''], 
    'nicht zugeordnet': [''],
}



FILENAME_PATTERN = "../data/%s"


def download_file(url, filename, use_cache=True):
    if use_cache:
        if os.path.exists(filename):
            return True

    print("requesting %s" % url)
    res = requests.get(url)

    filepath = os.path.dirname(filename)
    if not os.path.exists(filepath):
        print("creating directory %s" % filepath)
        os.makedirs(filepath)

    print("saving %s" % filename)
    data = res.content
    if data and data[0] >= 128:  # there's a strange character in front!?
        data = res.content[3:]
    with open(filename, "wb") as fp:
        fp.write(data)

    return True


def load_json(filename, url):
    filename = FILENAME_PATTERN % filename
    download_file(url, filename)
    with open(filename) as fp:
        data = json.load(fp)
    return data


def load_pandas_bmwahl(fileid):
    exclude_indicators = {
        "Von 102 Wahllokalen sind ausgezählt",
        "Stimmenmehrheit",
        "Wahlbeteiligung",
    }
    data = load_json(DATA_FILES[fileid]["filename"], DATA_FILES[fileid]["url"])
    geographies = data["geographies"][0]

    dic = OrderedDict({
        "Bezirk": [f["name"] for f in geographies["features"][1:]],
    })
    for theme in geographies["themes"]:
        for indicator in theme["indicators"]:
            if indicator["name"] in exclude_indicators:
                continue

            for associate in indicator["associates"]:
                if associate["type"] == "numeric":
                    break

            values = associate["values"]
            for i, v in enumerate(indicator["values"]):
                if isinstance(v, int):
                    values[i] = v

            dic[indicator["name"]] = [0 if not isinstance(v, int) else int(v) for v in values[1:]]

    df = pd.DataFrame(dic)
    df.index = df["Bezirk"]
    del df["Bezirk"]
    return df


def load_pandas_stat():

    data = load_json(DATA_FILES["stats-index"]["filename"], DATA_FILES["stats-index"]["url"])

    geographies = data["geographies"][0]
    dic = OrderedDict({
        "Bezirk": [f["name"] for f in geographies["features"]],
    })

    for theme in geographies["themes"]:
        url_part = theme["fileName"].split("/")[-1]
        fileid = "stat-%(themeId)s" % theme

        data = load_json("%s.json" % fileid,
                         "http://statistiken.jena.de/instantatlas/stadtbezirksstatistik/%s" % url_part)
        for indicator in data["indicators"]:
            dic["%(name)s(%(date)s)" % indicator] = indicator["values"]

    df = pd.DataFrame(dic)
    df.index = df["Bezirk"]
    del df["Bezirk"]
    return df


if __name__ == "__main__":

    if 0:
        for f in DATA_FILES:
            if f.startswith("bm"):
                load_pandas_bmwahl(f)

        load_pandas_stat()

    if 1:
        def load_polygons(fileid):
            data = load_json(DATA_FILES[fileid]["filename"], DATA_FILES[fileid]["url"])
            print(data)
        load_polygons("bm-shape")