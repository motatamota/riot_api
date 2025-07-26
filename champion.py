# champion.py  ※変更済み完全版
import requests
import re
import sys
import urllib.parse

DD_BASE = "https://ddragon.leagueoflegends.com"

# --- ★ 追加: タグ除去用ヘルパ ---
_TAG_RE = re.compile(r"<[^>]+>")

def strip_tags(text: str) -> str:
    """<font ...> や <br> など HTML ライクなタグをすべて削除"""
    return _TAG_RE.sub("", text)
# ---------------------------------

def _get_json(url: str):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def _latest_version() -> str:
    return _get_json(f"{DD_BASE}/api/versions.json")[0]

def _load_champion_list(ver: str):
    return _get_json(f"{DD_BASE}/cdn/{ver}/data/ja_JP/champion.json")["data"]

def _find_champion(champ_list: dict, query: str):
    q = query.lower()
    for cid, info in champ_list.items():
        if q == info["id"].lower() or q == info["name"].lower():
            return cid
    return None

def _load_champion_detail(ver: str, cid: str):
    url = f"{DD_BASE}/cdn/{ver}/data/ja_JP/champion/{urllib.parse.quote(cid)}.json"
    return _get_json(url)["data"][cid]

def _print_stats(info: dict):
    s = info["stats"]
    print("\n=== 基本ステータス (Lv1) ===")
    print(f"HP          : {s['hp']} (+{s['hpperlevel']}/Lv)")
    print(f"MP/Energy   : {s['mp']} (+{s['mpperlevel']}/Lv)")
    print(f"AttackDamage: {s['attackdamage']} (+{s['attackdamageperlevel']}/Lv)")
    print(f"Armor       : {s['armor']} (+{s['armorperlevel']}/Lv)")
    print(f"Magic Resist: {s['spellblock']} (+{s['spellblockperlevel']}/Lv)")
    print(f"Attack Speed: {s['attackspeed']:.3f} (+{s['attackspeedperlevel']:.3f}%)")
    print(f"Move Speed  : {s['movespeed']}")
    print(f"Range       : {s['attackrange']}")

def _print_skills(info: dict):
    print("\n=== スキル ===")
    passive = info["passive"]
    print(f"Passive – {passive['name']}\n  {strip_tags(passive['description'])}\n")
    for idx, spell in enumerate(info["spells"], start=1):
        key = "QWER"[idx-1]
        print(f"{key} – {spell['name']}")
        print(strip_tags(spell["description"]))
        print("")

def _find_candidates(champ_list: dict, query: str):
    """日本語・英語の部分一致で候補を返す（大文字小文字無視）"""
    q = query.lower()
    cands = []
    for cid, info in champ_list.items():
        if q in info["name"].lower() or q in info["id"].lower():
            cands.append((cid, info["name"]))
    return cands

def champion_menu():
    try:
        query = input("チャンピオン名 (日本語 or 英語／部分可) > ").strip()
        if not query:
            print("入力が空です。\n")
            return

        ver = _latest_version()
        champ_list = _load_champion_list(ver)

        # --- ★ 追加: 候補リスト作成 ---
        cands = _find_candidates(champ_list, query)
        if not cands:
            print("該当するチャンピオンが見つかりません。\n")
            return
        if len(cands) > 1:
            print("\n候補:")
            for idx, (_, jp_name) in enumerate(cands, 1):
                print(f"{idx}) {jp_name}")
            sel = input("番号を選択 > ").strip()
            if not sel.isdigit() or not (1 <= int(sel) <= len(cands)):
                print("無効な番号です。\n")
                return
            cid = cands[int(sel) - 1][0]
        else:
            cid = cands[0][0]
        # ---------------------------------

        info = _load_champion_detail(ver, cid)

        print(f"\n=== {info['name']} – {info['title']} ===")
        _print_stats(info)
        _print_skills(info)

    except requests.exceptions.RequestException as e:
        print("ネットワークエラー:", e, "\n")
    except Exception as e:
        print("エラー:", e, "\n")
