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


def load_json(fileid):
    filename = FILENAME_PATTERN % DATA_FILES[fileid]["filename"]
    download_file(DATA_FILES[fileid]["url"], filename)
    with open(filename) as fp:
        data = json.load(fp)
    return data


def load_pandas_bmwahl(fileid):
    exclude_indicators = {
        "Von 102 Wahllokalen sind ausgezählt",
        "Stimmenmehrheit",
        "Wahlbeteiligung",
    }
    data = load_json(fileid)
    geographies = data["geographies"][0]

    dic = OrderedDict({
        "Bezirk": ["%(name)s" % f for f in geographies["features"][1:]],
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


def load_pandas_stat(year=None):
    if year is not None:
        year = str(year)

    data = load_json("stats-index")

    geographies = data["geographies"][0]
    dic = OrderedDict({
        "Bezirk": [f["name"] for f in geographies["features"]],
    })

    for theme in geographies["themes"]:
        url_part = theme["fileName"].split("/")[-1]
        fileid = "stat-%(themeId)s" % theme
        DATA_FILES[fileid] = {
            "filename": "%s.json" % fileid,
            "url": "http://statistiken.jena.de/instantatlas/stadtbezirksstatistik/%s" % url_part
        }
        data = load_json(fileid)
        for indicator in data["indicators"]:
            if year is not None and indicator["date"] != year:
                continue
            dic["%(name)s(%(date)s)" % indicator] = indicator["values"]

    df = pd.DataFrame(dic)
    df.index = df["Bezirk"]
    del df["Bezirk"]
    return df


def calc_bmwahl_percent(bm):
    df = bm.copy()
    # Stimmen für Parteien in Prozent der gültigen Stimmen
    for col in bm.columns:
        if not col.startswith("n"):
            df[col] = df[col] / df["ng"].clip(1) * 100
    # gültige und ungültige Stimmen in Prozent der Wähler
    df["ng"] = df["ng"] / df["nw"].clip(1) * 100
    df["nu"] = df["nu"] / df["nw"].clip(1) * 100
    # Wähler in Prozent der Wahlberechtigten
    if max(df["n"]):
        df["nw"] = df["nw"] / df["n"].clip(1) * 100
    return df


def rename_bmwahl(df):
    mapping = {
        "Wahlberechtigte": "n",
        "Wähler": "nw",
        "ungültige Stimmen": "nu",
        'gültige Stimmen': "ng",
        'Benjamin Koppe': "CDU",
        'Martina Flämmich-Winckler': "LINKE",
        'Dr. Albrecht Schröter': "SPD",
        'Denny Jankowski': "AFD",
        'Denis Peisker': "GRÜNE",
        'Dr. Thomas Nitzsche': "FDP",
        'Dr. Heidrun Jänchen': "πRATEN",
        'Sandro Dreßler': "SANDRO",
        'Arne Petrich': "ARNE",
    }
    return df.copy().rename(columns={c:mapping.get(c, c) for c in df.columns})


def get_bmwahl_by_stats(bm):
    """Reorganize voting-data in bm to the structure of the Statistikbezirke using overlapping polygons"""
    from .geodata import GeoData
    geo = GeoData("bm-shape")
    geo2 = GeoData("stats-shape")

    bm_poly_map = {str(int(k.split()[0])):bm.loc[k] for k in bm.index}

    #df = pd.DataFrame(columns=bm.columns, index="Bezirk")
    skey_sum_dic = dict()
    for wkey in geo.polygons:
        wpoly = geo.polygons[wkey]
        row = bm_poly_map[wkey]
        for skey in geo2.polygons:
            spoly = geo2.polygons[skey]
            if spoly["polygon"].intersects(wpoly["polygon"]):
                try:
                    intersection = spoly["polygon"].intersection(wpoly["polygon"])
                    shared_area = intersection.area
                except:
                    shared_area = 0
                if skey not in skey_sum_dic:
                    skey_sum_dic[skey] = [0] * bm.shape[0]
                sums = skey_sum_dic[skey]
                fac = shared_area / wpoly["area"]
                for i, val in enumerate(row):
                    sums[i] += int(round(val * fac))

    df = pd.DataFrame({bm.columns[x]: [skey_sum_dic[skey][x] for y, skey in enumerate(sorted(skey_sum_dic))]
                       for x in range(len(bm.columns))},
                      index=sorted(skey_sum_dic), columns=bm.columns)
    #print(skey, wkey)
    return df


if __name__ == "__main__":

    if 0:
        for f in DATA_FILES:
            if f.startswith("bm"):
                load_pandas_bmwahl(f)

        load_pandas_stat()
