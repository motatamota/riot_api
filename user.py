# user.py  ── プラットフォームだけ聞いて region を自動判定する版
import os
import sys
import urllib.parse
import requests
from typing import Dict, List

API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
	sys.exit("環境変数 RIOT_API_KEY が未設定です。")

HEADERS = {"X-Riot-Token": API_KEY}

# -------- プラットフォームコード → regional routing 変換表 ----------
PLATFORM_TO_REGION = {
	# Asia クラスタ
	"jp1": "asia",
	"kr":  "asia",
	"oc1": "asia",
	# Americas クラスタ
	"na1": "americas",
	"br1": "americas",
	"la1": "americas",
	"la2": "americas",
	# Europe クラスタ
	"euw1": "europe",
	"eun1": "europe",
	"tr1":  "europe",
	"ru":   "europe",
}
# -------------------------------------------------------------------

def _get_json(url: str, params=None):
	r = requests.get(url, headers=HEADERS, params=params, timeout=10)
	if r.status_code != 200:
		raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
	return r.json()

def fetch_champion_dict() -> Dict[int, str]:
	version = _get_json("https://ddragon.leagueoflegends.com/api/versions.json")[0]
	data = _get_json(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json")
	return {int(v["key"]): k for k, v in data["data"].items()}

def prompt_riot_id() -> tuple[str, str]:
	while True:
		riot_id = input("Riot ID (例 Hide on bush#JP1) > ").strip()
		if "#" in riot_id:
			return riot_id.split("#", 1)
		print("形式が正しくありません。再入力してください。")

def prompt_platform() -> str:
	while True:
		p = input("プラットフォームコード (例 jp1 / kr / na1 ...) > ").strip().lower()
		if p in PLATFORM_TO_REGION:
			return p
		print("未知のプラットフォームコードです。")

def get_puuid(game_name: str, tag_line: str, region: str) -> str:
	url = (f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
		   f"{urllib.parse.quote(game_name)}/{urllib.parse.quote(tag_line)}")
	return _get_json(url)["puuid"]

def get_summoner(puuid: str, platform: str) -> dict:
	url = f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
	return _get_json(url)

def get_rank(puuid: str, platform: str) -> str:
	url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
	data = _get_json(url)
	solo = next((e for e in data if e["queueType"] == "RANKED_SOLO_5x5"), None)
	e = solo or (data[0] if data else None)
	return f"{e['tier']} {e['rank']} ({e['leaguePoints']} LP)" if e else "Unranked"

def top_masteries(puuid: str, platform: str,
				  champ_dict: Dict[int, str], n=3) -> List[str]:
	url = f"https://{platform}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
	return [f"{champ_dict.get(m['championId'], m['championId'])} ({m['championPoints']})"
			for m in _get_json(url)[:n]]

def recent_results(puuid: str, region: str, count=10) -> str:
	ids_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
	match_ids = _get_json(ids_url, params={"start": 0, "count": count})
	results = []
	for mid in match_ids:
		info = _get_json(f"https://{region}.api.riotgames.com/lol/match/v5/matches/{mid}")["info"]
		win = next(p["win"] for p in info["participants"] if p["puuid"] == puuid)
		results.append("W" if win else "L")
	return " ".join(results)

# ---------------------------------------------------- メニュー入口
def user_menu():
	try:
		game_name, tag_line = prompt_riot_id()
		platform = prompt_platform()                 # jp1 / kr / na1 ...
		region = PLATFORM_TO_REGION[platform]        # asia / americas / europe

		puuid = get_puuid(game_name, tag_line, region)
		summ  = get_summoner(puuid, platform)
		champ_dict = fetch_champion_dict()

		print("\n=== サモナー情報 ===")
		print(f"SummonerName : {game_name}")
		print(f"Level        : {summ['summonerLevel']}")
		# print(f"PUUID        : {puuid}")
		print(f"Rank         : {get_rank(puuid, platform)}\n")

		print("--- マスタリー TOP3 ---")
		for line in top_masteries(puuid, platform, champ_dict):
			print("・", line)

		print("\n--- 直近10戦 (W/L) ---")
		print(recent_results(puuid, region))
		print("")

	except Exception as e:
		print("エラー:", e)
