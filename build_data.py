"""Build data.js for the War Thunder research calculator from the community datamine.

Run: python3 build_data.py
Output: data.js (window.WT_DATA = {...}), loaded by index.html.
"""
import csv
import io
import json
import re
import urllib.request
from datetime import date

BASE = "https://raw.githubusercontent.com/gszabi99/War-Thunder-Datamine/master/"
# Game-font icon glyphs (nation markers, event symbols) that render as junk outside the game.
ICON_GLYPHS = re.compile("[\u22e0\u2400-\u243f\u2580-\u25ff\ue000-\uf8ff]")
# shop.blkx branch -> rank.blkx unit type in needBuyToOpenNextInEra<Type><rank>.
RANK_TYPES = {"army": "Tank", "aviation": "Aircraft", "helicopters": "Helicopter", "ships": "Ship", "boats": "Boat"}
PREMIUM_KEYS = ("gift", "event", "marketplaceItemdefId", "isClanVehicle", "showOnlyWhenBought")


def fetch(path):
    with urllib.request.urlopen(BASE + path) as r:
        return r.read().decode("utf-8")


def load_names():
    rows = csv.reader(io.StringIO(fetch("lang.vromfs.bin_u/lang/units.csv")), delimiter=";")
    header = next(rows)
    en, ko = header.index("<English>"), header.index("<Korean>")
    names = {}
    for row in rows:
        if len(row) <= ko:
            continue
        if row[0].startswith("shop/group/"):  # folder names
            names[row[0][len("shop/group/"):]] = tuple(ICON_GLYPHS.sub("", row[i].replace("\u200b", "")).strip() for i in (en, ko))
        elif row[0].endswith("_shop"):
            names[row[0][:-5]] = tuple(ICON_GLYPHS.sub("", row[i].replace("\u200b", "")).strip() for i in (en, ko))
    return names


def rank_requirements(rank):
    """{country: {branch: [n1, n2, ...]}}: n_r = vehicles of rank r needed to open rank r+1."""
    out = {}
    for country, keys in rank["needBuyToOpenNextInEra"].items():
        for branch, kind in RANK_TYPES.items():
            prefix = "needBuyToOpenNextInEra" + kind
            counts = sorted((int(k[len(prefix):]), n) for k, n in keys.items() if k.startswith(prefix) and k[len(prefix):].isdigit())
            out.setdefault(country, {})[branch] = [n for _, n in counts]
    return out


def build(shop, cost, names):
    units, trees, groups = {}, {}, {}

    def add(uid, info, req, premium):
        c = cost.get(uid, {})
        en, ko = names.get(uid, (uid, uid))
        units[uid] = {
            "rank": info.get("rank") or c.get("rank", 0),
            "rp": c.get("reqExp", 0),
            "sl": c.get("value", 0),
            "train": c.get("trainCost", 0),
            "premium": premium,
            "en": en,
            "ko": ko,
            "req": req,
        }

    def is_premium(uid, info):
        return any(k in info for k in PREMIUM_KEYS) or "costGold" in cost.get(uid, {})

    for country, branches in shop.items():
        for branch, tree in branches.items():
            columns = []
            for col in tree.get("range", []):
                items, prev = [], None
                for key, info in col.items():
                    subs = [(k, v) for k, v in info.items() if isinstance(v, dict)]
                    group = subs or [(key, info)]
                    ids, folder_top = [], None
                    for i, (uid, uinfo) in enumerate(group):
                        # Folder-level reqAir applies to the first vehicle inside the folder.
                        rule = info if (subs and i == 0) else uinfo
                        premium = is_premium(uid, uinfo) or is_premium(key, info)
                        if premium:
                            req = None
                        elif "reqAir" in rule:
                            req = rule["reqAir"] or None  # "" = no prerequisite, rank unlock only
                        else:
                            req = prev
                        add(uid, uinfo, req, premium)
                        if not premium:
                            prev = uid
                            folder_top = folder_top or uid
                        ids.append(uid)
                    # Inside a folder each vehicle needs the one above it; the vehicle after
                    # the folder needs only the folder's top vehicle.
                    if subs and folder_top:
                        prev = folder_top
                    if subs:
                        en, ko = names.get(key, ("/".join(units[i]["en"] for i in ids),) * 2)
                        groups[key] = {"en": en, "ko": ko}
                        items.append({"group": key, "ids": ids})
                    else:
                        items.append(ids[0])
                columns.append(items)
            trees.setdefault(country, {})[branch] = columns
    return {"updated": date.today().isoformat(), "trees": trees, "units": units, "groups": groups}


def check(data):
    u = data["units"]
    assert u["us_m5a1_stuart"]["req"] is None, u["us_m5a1_stuart"]
    assert u["us_m24_chaffee"]["req"] == "us_m5a1_stuart", u["us_m24_chaffee"]
    assert u["us_m4_sherman"]["req"] == "us_m4a1_1942_sherman", u["us_m4_sherman"]
    assert u["us_m4a2_sherman"]["req"] == "us_m4_sherman", u["us_m4a2_sherman"]
    assert u["us_m4a1_76w_sherman"]["req"] == "us_m4a1_1942_sherman", u["us_m4a1_76w_sherman"]
    assert data["groups"]["us_sherman_group"]["en"] == "M4A1/M4/M4A2", data["groups"]["us_sherman_group"]
    assert not any(ICON_GLYPHS.search(x["en"] + x["ko"]) for x in u.values())
    assert data["rankReq"]["country_usa"]["army"][0] == 6, data["rankReq"]["country_usa"]["army"]
    assert u["us_m24_chaffee"]["rp"] > 0 and u["us_lvt_a_4"]["premium"]


def main():
    shop = json.loads(fetch("char.vromfs.bin_u/config/shop.blkx"))
    cost = json.loads(fetch("char.vromfs.bin_u/config/wpcost.blkx"))
    data = build(shop, cost, load_names())
    data["rankReq"] = rank_requirements(json.loads(fetch("char.vromfs.bin_u/config/rank.blkx")))
    check(data)
    with open("data.js", "w", encoding="utf-8") as f:
        f.write("window.WT_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"{len(data['units'])} vehicles written to data.js")


if __name__ == "__main__":
    main()
